import asyncio
from app.core.database import engine, Base

# Import all models to ensure they are registered with Base.metadata
from app.models.personnel import ServiceMember
from app.models.cases import Case
from app.models.injuries import Injury
from app.models.medications import MedicationAdministration
from app.models.vitals import VitalsObservation
from app.models.procedures import Procedure
from app.models.march import MarchAssessment
from app.models.evacuation import EvacuationRecord
from app.models.events import Event
from app.models.documents import CaseDocument
from app.models.user import User
from app.models.idempotency import IdempotencyRecord
from app.models.sync_queue import SyncQueue
from app.models.audit import AuditLog
from app.models.field_drop import (
    FieldPosition,
    FieldInventoryItem,
    FieldSupplyRequest,
    FieldSupplyNeed,
    FieldDispatchLog,
)

async def init_db():
    async with engine.begin() as conn:
        print("🔧 Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database initialized successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
