"""Integration test: handoff payload includes MARCH notes."""
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.core.database import Base, get_session
from app.models.cases import Case
from app.models.march import MarchAssessment

# Ensure all table metadata is registered before create_all.
import app.models.audit  # noqa: F401
import app.models.documents  # noqa: F401
import app.models.evacuation  # noqa: F401
import app.models.events  # noqa: F401
import app.models.field_drop  # noqa: F401
import app.models.idempotency  # noqa: F401
import app.models.injuries  # noqa: F401
import app.models.medications  # noqa: F401
import app.models.personnel  # noqa: F401
import app.models.procedures  # noqa: F401
import app.models.sync_queue  # noqa: F401
import app.models.user  # noqa: F401
import app.models.vitals  # noqa: F401


@pytest_asyncio.fixture
async def handoff_client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from backend.main import app as fastapi_app

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_session():
        async with SessionLocal() as session:
            yield session

    async def override_get_current_user():
        return {"sub": "test-user", "device_id": "test-dev", "role": "admin", "unit": "HQ"}

    fastapi_app.dependency_overrides[get_session] = override_get_session
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as client:
        yield client, engine

    await engine.dispose()
    fastapi_app.dependency_overrides.pop(get_session, None)
    fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_generate_handoff_includes_march_notes(handoff_client):
    client, engine = handoff_client
    case_id = str(uuid.uuid4())

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Case(
                id=case_id,
                callsign="CASE-001",
                triage_code="IMMEDIATE",
                case_status="ACTIVE",
            )
        )
        session.add(
            MarchAssessment(
                id=str(uuid.uuid4()),
                case_id=case_id,
                m_notes="massive bleeding controlled",
                a_notes="airway patent",
                r_notes="breathing stable",
                c_notes="pulse present",
                h_notes="hypothermia prevented",
            )
        )
        await session.commit()

    response = await client.post(f"/api/v1/cases/{case_id}/handoff/generate")

    assert response.status_code == 200
    payload = response.json()["data"]
    treatment = payload["treatment"]
    march_notes = treatment["march_notes"]

    assert march_notes["m_notes"] == "massive bleeding controlled"
    assert march_notes["a_notes"] == "airway patent"
    assert march_notes["r_notes"] == "breathing stable"
    assert march_notes["c_notes"] == "pulse present"
    assert march_notes["h_notes"] == "hypothermia prevented"
