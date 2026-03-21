"""Integration test: export bundle contains MARCH notes."""
import io
import json
import uuid
import zipfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.core.database import Base, get_session
from app.models.cases import Case
from app.models.march import MarchAssessment

# Ensure metadata registration before create_all.
import app.models.audit  # noqa: F401
import app.models.documents  # noqa: F401
import app.models.evacuation  # noqa: F401
import app.models.events  # noqa: F401
import app.models.field_drop  # noqa: F401
import app.models.form100  # noqa: F401
import app.models.idempotency  # noqa: F401
import app.models.injuries  # noqa: F401
import app.models.medications  # noqa: F401
import app.models.personnel  # noqa: F401
import app.models.procedures  # noqa: F401
import app.models.sync_queue  # noqa: F401
import app.models.user  # noqa: F401
import app.models.vitals  # noqa: F401


@pytest_asyncio.fixture
async def export_client():
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
async def test_export_bundle_includes_march_notes(export_client):
    client, engine = export_client
    case_id = str(uuid.uuid4())

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Case(
                id=case_id,
                callsign="CASE-EXPORT-001",
                triage_code="IMMEDIATE",
                case_status="ACTIVE",
                mechanism_of_injury="BLAST",
            )
        )
        session.add(
            MarchAssessment(
                id=str(uuid.uuid4()),
                case_id=case_id,
                m_notes="m note",
                a_notes="a note",
                r_notes="r note",
                c_notes="c note",
                h_notes="h note",
            )
        )
        await session.commit()

    response = await client.get(f"/api/v1/exports/{case_id}/bundle")

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/zip")

    archive = zipfile.ZipFile(io.BytesIO(response.content), mode="r")
    case_json = json.loads(archive.read("case.json").decode("utf-8"))

    assert "march_notes" in case_json
    assert case_json["march_notes"]["m_notes"] == "m note"
    assert case_json["march_notes"]["a_notes"] == "a note"
    assert case_json["march_notes"]["r_notes"] == "r note"
    assert case_json["march_notes"]["c_notes"] == "c note"
    assert case_json["march_notes"]["h_notes"] == "h note"
