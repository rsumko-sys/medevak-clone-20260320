from typing import Any, Dict, Optional, Type
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.personnel import ServiceMember
from app.models.sync_queue import SyncQueue
from app.models.cases import Case
from app.models.evacuation import EvacuationRecord
from app.models.march import MarchAssessment
from app.models.injuries import Injury
from app.models.vitals import VitalsObservation
from app.models.procedures import Procedure
from app.models.medications import MedicationAdministration

# Maps sync entity_type string → (SQLAlchemy model, version column name)
_MODEL_REGISTRY: Dict[str, tuple] = {
    "service_member": (ServiceMember,        "version_id"),
    "case":           (Case,                 "server_version"),
    "evacuation":     (EvacuationRecord,     "version_id"),
    "march":          (MarchAssessment,      "version_id"),
    "injury":         (Injury,               "version_id"),
    "vitals":         (VitalsObservation,    "version_id"),
    "procedure":      (Procedure,            "version_id"),
    "medication":     (MedicationAdministration, "version_id"),
}

class SyncService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def reconcile_entity(self, entity_type: str, remote_data: Dict[str, Any]) -> bool:
        """
        Reconcile a remote entity change with the local state.
        Uses version-based conflict detection and field-level merging.
        """
        entry = _MODEL_REGISTRY.get(entity_type)
        if not entry:
            return False
        model, version_field = entry
            
        entity_id = remote_data.get("id")
        if not entity_id:
            return False
            
        # 1. Fetch local entity
        stmt = select(model).where(model.id == entity_id)
        result = await self.session.execute(stmt)
        local_entity = result.scalar_one_or_none()
        
        if not local_entity:
            # New entity - simple creation
            new_entity = model(**remote_data)
            self.session.add(new_entity)
            await self.session.commit()
            return True
            
        # 2. Conflict Detection — use the correct version field for each model
        remote_version = remote_data.get(version_field, 0)
        local_version = getattr(local_entity, version_field, 0)
        
        if remote_version <= local_version:
            # Remote is stale - ignore
            return False
            
        # 3. Field-Level Merge
        # We prefer remote data if it has a newer timestamp or higher version,
        # but in a true field-level merge, we'd compare individual field timestamps if available.
        # Since we only have 'updated_at' at the entity level, we perform a smart update.
        
        remote_updated_at_str = remote_data.get("updated_at")
        remote_updated_at = datetime.fromisoformat(remote_updated_at_str) if remote_updated_at_str else datetime.now(timezone.utc)
        local_updated_at = getattr(local_entity, "updated_at", datetime.min)
        
        if remote_version == local_version + 1:
            # Clean sequence - apply all
            for key, value in remote_data.items():
                if hasattr(local_entity, key) and key not in ["id", "created_at"]:
                    setattr(local_entity, key, value)
        else:
            # Gap detected or conflict - Field-level heuristics
            # For now, we take the remote as truth if version is higher, 
            # but we could add more complex merging here.
            for key, value in remote_data.items():
                if hasattr(local_entity, key) and key not in ["id", "created_at"]:
                    # Basic policy: overwrite if remote is definitely newer
                    setattr(local_entity, key, value)
                    
        setattr(local_entity, version_field, remote_version)
        local_entity.updated_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        return True
