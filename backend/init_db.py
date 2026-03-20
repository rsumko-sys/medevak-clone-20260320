import asyncio
from backend.app.core.database import engine, Base

# Import all models to ensure they are registered with Base.metadata
from backend.app.models.personnel import ServiceMember
from backend.app.models.cases import Case
from backend.app.models.injuries import Injury
from backend.app.models.medications import MedicationAdministration
from backend.app.models.vitals import VitalsObservation
from backend.app.models.procedures import Procedure
from backend.app.models.march import MarchAssessment
from backend.app.models.evacuation import EvacuationRecord
from backend.app.models.events import Event
from backend.app.models.documents import CaseDocument
from backend.app.models.user import User
from backend.app.models.idempotency import IdempotencyRecord
from backend.app.models.sync_queue import SyncQueue
from backend.app.models.audit import AuditLog

async def init_db():
    async with engine.begin() as conn:
        print("🔧 Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database initialized successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
