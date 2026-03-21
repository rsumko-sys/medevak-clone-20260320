"""Integration tests: Form 100 appears in export bundle and PDF output."""
import io
import json
import uuid
import zipfile
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.core.database import Base, get_session
from app.models.cases import Case
from app.models.form100 import Form100Record

# Ensure metadata registration before create_all.
import app.models.audit  # noqa: F401
import app.models.documents  # noqa: F401
import app.models.evacuation  # noqa: F401
import app.models.events  # noqa: F401
import app.models.field_drop  # noqa: F401
import app.models.idempotency  # noqa: F401
import app.models.injuries  # noqa: F401
import app.models.march  # noqa: F401
import app.models.medications  # noqa: F401
import app.models.personnel  # noqa: F401
import app.models.procedures  # noqa: F401
import app.models.sync_queue  # noqa: F401
import app.models.user  # noqa: F401
import app.models.vitals  # noqa: F401


@pytest_asyncio.fixture
async def export_form100_client():
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
async def test_export_bundle_and_pdf_include_form100(export_form100_client):
    client, engine = export_form100_client
    case_id = str(uuid.uuid4())

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Case(
                id=case_id,
                callsign="CASE-EXPORT-F100",
                triage_code="IMMEDIATE",
                case_status="ACTIVE",
            )
        )
        session.add(
            Form100Record(
                id=str(uuid.uuid4()),
                case_id=case_id,
                document_number="F100-EXP-01",
                injury_datetime=datetime(2026, 3, 21, 10, 15, 0),
                injury_location="Sector B",
                injury_mechanism="GSW",
                diagnosis_summary="Penetrating trauma",
                documented_by="Medic-02",
                front_side_triage_markers_json=json.dumps({"red_urgent_care": True}),
                back_side_stage_log_json=json.dumps([
                    {"stage_name": "ROLE_1", "result": "stable"},
                    {"stage_name": "ROLE_2", "result": "evacuate"},
                ]),
            )
        )
        await session.commit()

    bundle_resp = await client.get(f"/api/v1/exports/{case_id}/bundle")
    assert bundle_resp.status_code == 200

    archive = zipfile.ZipFile(io.BytesIO(bundle_resp.content), mode="r")
    case_json = json.loads(archive.read("case.json").decode("utf-8"))
    assert "form_100" in case_json
    assert case_json["form_100"]["document_number"] == "F100-EXP-01"
    assert case_json["form_100"]["injury_location"] == "Sector B"
    assert case_json["form_100"]["front_side"]["triage_markers"]["red_urgent_care"] is True
    assert len(case_json["form_100"]["back_side"]["stage_log"]) == 2

    pdf_resp = await client.get(f"/api/v1/exports/{case_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.content.startswith(b"%PDF")
    # Validate Form 100 is rendered by checking a unique field token in PDF bytes.
    assert b"F100-EXP-01" in pdf_resp.content
