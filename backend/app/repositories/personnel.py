"""Optimized personnel repository with eager loading."""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload

from app.models.personnel import (
    ServiceMember, 
    PersonnelRecord, 
    MedicalRecord, 
    DeploymentRecord,
    PersonnelDocument
)
from app.models.cases import Case


class PersonnelRepository:
    """Repository for optimized personnel operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id_all_relations(
        self, 
        member_id: str,
        unit: Optional[str] = None,
        include_deleted: bool = False,
        include_medical: bool = False,
        include_deployments: bool = False,
        include_personnel: bool = False,
        include_documents: bool = False
    ) -> Optional[ServiceMember]:

        """Get service member with optimized eager loading."""
        
        # Build query with eager loading
        stmt = select(ServiceMember)
        
        # Add eager loading based on requirements
        eager_loads = []
        
        if include_medical:
            eager_loads.append(selectinload(ServiceMember.medical_records))
        
        if include_deployments:
            eager_loads.append(selectinload(ServiceMember.deployment_records))
        
        if include_personnel:
            eager_loads.append(selectinload(ServiceMember.personnel_records))
        
        if include_documents:
            eager_loads.append(selectinload(ServiceMember.documents))
        
        # Apply eager loading
        for load in eager_loads:
            stmt = stmt.options(load)
        
        # Filter by ID
        filters = [ServiceMember.id == member_id]
        
        # QLAC: Unit isolation
        if unit:
            filters.append(ServiceMember.unit == unit)
            
        # QLAC: Soft-delete consistency
        if not include_deleted:
            filters.append(ServiceMember.is_deleted == False)
            
        stmt = stmt.where(and_(*filters))

        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_with_filters(
        self,
        filters: Optional[List] = None,
        unit: Optional[str] = None,
        rank: Optional[str] = None,
        status: Optional[str] = None,
        is_deployed: Optional[bool] = None,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[ServiceMember]:

        """List service members with optimized filtering."""
        
        query = select(ServiceMember)
        
        # Base QLAC filters
        qlac_filters = []
        if not include_deleted:
            qlac_filters.append(ServiceMember.is_deleted == False)
        
        if filters:
            qlac_filters.extend(filters)
            
        if qlac_filters:
            query = query.where(and_(*qlac_filters))

        
        # Apply common filters
        if unit:
            query = query.where(ServiceMember.unit.ilike(f"%{unit}%"))
        
        if rank:
            query = query.where(ServiceMember.rank.ilike(f"%{rank}%"))
        
        if status:
            query = query.where(ServiceMember.status == status)
        
        if is_deployed is not None:
            query = query.where(ServiceMember.is_deployed == is_deployed)
        
        # Apply ordering
        if hasattr(ServiceMember, order_by):
            order_column = getattr(ServiceMember, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_with_filters(
        self,
        filters: Optional[List] = None,
        unit: Optional[str] = None,
        rank: Optional[str] = None,
        status: Optional[str] = None,
        is_deployed: Optional[bool] = None
    ) -> int:
        """Count service members with filters (optimized)."""
        
        query = select(func.count(ServiceMember.id))
        
        # Apply same filters as list_with_filters
        if filters:
            query = query.where(and_(*filters))
        
        if unit:
            query = query.where(ServiceMember.unit.ilike(f"%{unit}%"))
        
        if rank:
            query = query.where(ServiceMember.rank.ilike(f"%{rank}%"))
        
        if status:
            query = query.where(ServiceMember.status == status)
        
        if is_deployed is not None:
            query = query.where(ServiceMember.is_deployed == is_deployed)
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def get_medical_records_by_member(
        self, 
        member_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[MedicalRecord]:
        """Get medical records for a member with pagination."""
        
        query = select(MedicalRecord).where(
            and_(
                MedicalRecord.service_member_id == member_id,
                MedicalRecord.is_deleted == False # Ensure soft-deleted records are hidden
            )
        ).order_by(MedicalRecord.encounter_date.desc()).offset(offset).limit(limit)

        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_deployment_records_by_member(
        self,
        member_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[DeploymentRecord]:
        """Get deployment records for a member with pagination."""
        
        query = select(DeploymentRecord).where(
            and_(
                DeploymentRecord.service_member_id == member_id,
                DeploymentRecord.is_deleted == False # Ensure soft-deleted records are hidden
            )
        ).order_by(DeploymentRecord.start_date.desc()).offset(offset).limit(limit)

        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_members(
        self,
        search_term: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[ServiceMember]:
        """Search service members by name, service number, or unit."""
        
        search_pattern = f"%{search_term}%"
        
        query = select(ServiceMember).where(
            and_(
                ServiceMember.is_deleted == False,
                or_(
                    ServiceMember.last_name.ilike(search_pattern),
                    ServiceMember.first_name.ilike(search_pattern),
                    ServiceMember.middle_name.ilike(search_pattern),
                    ServiceMember.service_number.ilike(search_pattern),
                    ServiceMember.unit.ilike(search_pattern)
                )
            )
        ).order_by(ServiceMember.last_name.asc()).offset(offset).limit(limit)

        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_members_by_unit(
        self,
        unit: str,
        include_details: bool = False
    ) -> List[ServiceMember]:
        """Get all members from specific unit with optional details."""
        
        query = select(ServiceMember).where(
            and_(
                ServiceMember.unit.ilike(f"%{unit}%"),
                ServiceMember.is_deleted == False
            )
        )

        
        if include_details:
            query = query.options(
                selectinload(ServiceMember.medical_records),
                selectinload(ServiceMember.deployment_records)
            )
        
        query = query.order_by(ServiceMember.rank.desc(), ServiceMember.last_name.asc())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_deployed_members(
        self,
        theater: Optional[str] = None
    ) -> List[ServiceMember]:
        """Get all currently deployed members."""
        
        query = select(ServiceMember).where(
            and_(
                ServiceMember.is_deployed == True,
                ServiceMember.is_deleted == False
            )
        )

        
        if theater:
            # Filter by deployment theater
            query = query.join(DeploymentRecord).where(
                DeploymentRecord.theater == theater
            )
        
        query = query.order_by(ServiceMember.unit.asc(), ServiceMember.rank.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_medical_statistics(
        self,
        unit: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get medical statistics for unit or all personnel."""
        
        query = select(ServiceMember).where(ServiceMember.is_deleted == False)
        
        if unit:
            query = query.where(ServiceMember.unit.ilike(f"%{unit}%"))

        
        # Get members
        result = await self.session.execute(query)
        members = result.scalars().all()
        
        # Calculate statistics
        total_members = len(members)
        deployed_count = sum(1 for m in members if m.is_deployed)
        combat_experience_count = sum(1 for m in members if m.combat_experience)
        
        # Blood type distribution
        blood_types = {}
        for member in members:
            if member.blood_type:
                blood_types[member.blood_type] = blood_types.get(member.blood_type, 0) + 1
        
        return {
            "total_members": total_members,
            "deployed_count": deployed_count,
            "combat_experience_count": combat_experience_count,
            "deployment_rate": (deployed_count / total_members * 100) if total_members > 0 else 0,
            "blood_type_distribution": blood_types,
            "units": list(set(m.unit for m in members if m.unit))
        }
    
    async def batch_create_members(
        self,
        members_data: List[Dict[str, Any]]
    ) -> List[ServiceMember]:
        """Batch create multiple members efficiently."""
        
        members = []
        for member_data in members_data:
            member = ServiceMember(**member_data)
            members.append(member)
        
        self.session.add_all(members)
        await self.session.commit()
        
        # Refresh to get IDs
        for member in members:
            await self.session.refresh(member)
        
        return members
    
    async def update_member_with_relations(
        self,
        member_id: str,
        update_data: Dict[str, Any],
        medical_updates: Optional[List[Dict[str, Any]]] = None,
        deployment_updates: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[ServiceMember]:
        """Update member and related records in single transaction."""
        
        try:
            # Get member with relations (Renamed call)
            member = await self.get_by_id_all_relations(
                member_id,
                include_medical=True,
                include_deployments=True
            )

            
            if not member:
                return None
            
            # Update main member data
            for field, value in update_data.items():
                if hasattr(member, field):
                    setattr(member, field, value)
            
            # Update medical records if provided
            if medical_updates:
                for med_data in medical_updates:
                    med_id = med_data.get("id")
                    if med_id:
                        # Update existing
                        med_record = next((m for m in member.medical_records if m.id == med_id), None)
                        if med_record:
                            for field, value in med_data.items():
                                if hasattr(med_record, field) and field != "id":
                                    setattr(med_record, field, value)
                    else:
                        # Create new
                        new_med = MedicalRecord(
                            service_member_id=member_id,
                            **med_data
                        )
                        member.medical_records.append(new_med)
            
            # Update deployment records if provided
            if deployment_updates:
                for dep_data in deployment_updates:
                    dep_id = dep_data.get("id")
                    if dep_id:
                        # Update existing
                        dep_record = next((d for d in member.deployment_records if d.id == dep_id), None)
                        if dep_record:
                            for field, value in dep_data.items():
                                if hasattr(dep_record, field) and field != "id":
                                    setattr(dep_record, field, value)
                    else:
                        # Create new
                        new_dep = DeploymentRecord(
                            service_member_id=member_id,
                            **dep_data
                        )
                        member.deployment_records.append(new_dep)

            
            await self.session.commit()
            await self.session.refresh(member)
            
            return member
            
        except Exception as e:
            await self.session.rollback()
            raise e
