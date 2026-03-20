"""Cases repository."""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.cases import Case
from app.models.vitals import VitalsObservation
from app.models.medications import MedicationAdministration
from app.models.procedures import Procedure



class CasesRepository:
    """Repository for Case operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, case_id: str) -> Optional[Case]:
        """Get case by ID."""
        result = await self.session.get(Case, case_id)
        return result
    
    async def get_all(self, filters: Optional[List] = None, limit: int = 100, offset: int = 0) -> List[Case]:
        """Get all cases with optional filters."""
        query = select(Case)
        if filters:
            query = query.where(and_(*filters))
        query = query.offset(offset).limit(limit).order_by(Case.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create(self, case_data: Dict[str, Any]) -> Case:
        """Create new case."""
        case = Case(**case_data)
        self.session.add(case)
        await self.session.commit()
        await self.session.refresh(case)
        return case
    
    async def update(self, case_id: str, case_data: Dict[str, Any]) -> Optional[Case]:
        """Update case."""
        case = await self.get_by_id(case_id)
        if not case:
            return None
        
        for field, value in case_data.items():
            if hasattr(case, field):
                setattr(case, field, value)
        
        await self.session.commit()
        await self.session.refresh(case)
        return case
    
    async def delete(self, case_id: str) -> bool:
        """Delete case."""
        case = await self.get_by_id(case_id)
        if not case:
            return False
        
        await self.session.delete(case)
        await self.session.commit()
        return True
