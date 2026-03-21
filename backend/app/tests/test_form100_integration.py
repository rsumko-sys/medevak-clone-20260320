"""Integration tests for Form 100 CRUD and case retrieval inclusion."""
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.core.database import Base, get_session
from app.models.cases import Case

# Ensure metadata registration before create_all.
import app.models.audit  # noqa: F401
import app.models.documents  # noqa: F401
import app.models.evacuation  # noqa: F401
import app.models.events  # noqa: F401
import app.models.field_drop  # noqa: F401
import app.models.form100  # noqa: F401
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
async def form100_client():
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
async def test_form100_create_read_update_and_case_detail_inclusion(form100_client):
    client, engine = form100_client
    case_id = str(uuid.uuid4())

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        session.add(Case(id=case_id, callsign="CASE-F100-1", triage_code="IMMEDIATE", case_status="ACTIVE"))
        await session.commit()

    create_payload = {
        "document_number": "F100-001",
        "injury_datetime": datetime(2026, 3, 21, 10, 15, tzinfo=timezone.utc).isoformat(),
        "injury_location": "Sector A",
        "injury_mechanism": "BLAST",
        "diagnosis_summary": "Multiple fragmentation wounds",
        "documented_by": "Medic-01",
        "treatment_summary": "Stabilized, analgesia given",
    }

    create_resp = await client.post(f"/api/v1/cases/{case_id}/form100", json=create_payload)
    assert create_resp.status_code == 200
    created = create_resp.json()["data"]
    assert created["document_number"] == "F100-001"
    assert created["injury_location"] == "Sector A"

    read_resp = await client.get(f"/api/v1/cases/{case_id}/form100")
    assert read_resp.status_code == 200
    read_data = read_resp.json()["data"]
    assert read_data["documented_by"] == "Medic-01"

    update_resp = await client.patch(
        f"/api/v1/cases/{case_id}/form100",
        json={"diagnosis_summary": "Updated diagnosis", "commander_notified": True},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]
    assert updated["diagnosis_summary"] == "Updated diagnosis"
    assert updated["commander_notified"] is True

    case_resp = await client.get(f"/api/v1/cases/{case_id}")
    assert case_resp.status_code == 200
    detail = case_resp.json()["data"]
    assert detail["form100"] is not None
    assert detail["form100"]["document_number"] == "F100-001"

    handoff_resp = await client.post(f"/api/v1/cases/{case_id}/handoff/generate")
    assert handoff_resp.status_code == 200
    treatment = handoff_resp.json()["data"]["treatment"]
    assert treatment["form100"] is not None
    assert treatment["form100"]["document_number"] == "F100-001"


@pytest.mark.asyncio
async def test_form100_canonical_nested_structure_and_stage_log_semantics(form100_client):
    client, engine = form100_client
    case_id = str(uuid.uuid4())

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        session.add(Case(id=case_id, callsign="CASE-F100-2", triage_code="IMMEDIATE", case_status="ACTIVE"))
        await session.commit()

    create_payload = {
        "document_number": "F100-NESTED-01",
        "stub": {
            "issued_at": datetime(2026, 3, 21, 9, 0, tzinfo=timezone.utc).isoformat(),
            "urgent_care_flag": True,
            "sanitary_processing_flag": True,
            "isolation_flag": False,
        },
        "front_side": {
            "identity": {
                "rank": "SGT",
                "unit_name": "Alpha",
                "full_name": "John Doe",
                "sex": "M",
            },
            "injury": {
                "injury_or_illness_datetime": datetime(2026, 3, 21, 8, 45, tzinfo=timezone.utc).isoformat(),
                "sanitary_loss_type": "combat",
                "injury_category_codes": ["FRAG", "BLAST"],
                "injury_mechanism": "BLAST",
                "diagnosis": "Multiple fragment wounds",
                "body_diagram_marks": [
                    {
                        "wound_mark_type": "entry",
                        "wound_mark_location": "Left thigh",
                        "wound_mark_notes": "Primary wound",
                    }
                ],
            },
            "treatment": {
                "antibiotic": "ceftriaxone",
                "painkiller": "ketorolac",
                "treatment_notes": "Analgesia and dressing",
            },
            "evacuation": {
                "evacuation_transport": "MEDEVAC",
                "evacuation_destination": "Role 2",
                "evacuation_position": "lying",
                "evacuation_priority": "urgent",
                "recommendation_notes": "Immediate evacuation",
            },
            "triage_markers": {
                "red_urgent_care": True,
                "yellow_sanitary_processing": True,
                "black_isolation": False,
                "blue_radiation_measures": False,
            },
            "body_diagram": {
                "body_diagram_marks": [
                    {
                        "wound_mark_type": "entry",
                        "wound_mark_location": "Left thigh",
                        "wound_mark_notes": "Diagram mark",
                    }
                ],
                "placeholder_model": "TODO:graphic-model-pending",
            },
        },
        "back_side": {
            "stage_log": [
                {
                    "arrived_at": datetime(2026, 3, 21, 9, 10, tzinfo=timezone.utc).isoformat(),
                    "stage_name": "ROLE_1",
                    "physician_notes": "Initial stabilization",
                    "result": "stable",
                },
                {
                    "arrived_at": datetime(2026, 3, 21, 10, 0, tzinfo=timezone.utc).isoformat(),
                    "stage_name": "ROLE_2",
                    "physician_notes": "Surgical consult",
                    "result": "evacuate",
                },
            ],
            "signature": {
                "physician_name": "Medic-Canonical",
                "physician_signature": "signed",
                "signed_at": datetime(2026, 3, 21, 10, 5, tzinfo=timezone.utc).isoformat(),
            },
        },
        "meta_legal_rules": {
            "legal_status": "official",
            "first_eme_completed": True,
            "continuity_required": True,
            "commander_notified": True,
            "additional_notes": "Legal continuity preserved",
        },
    }

    create_resp = await client.post(f"/api/v1/cases/{case_id}/form100", json=create_payload)
    assert create_resp.status_code == 200
    created = create_resp.json()["data"]

    # Canonical nested sections are persisted and returned.
    assert created["stub"]["urgent_care_flag"] is True
    assert created["front_side"]["triage_markers"]["yellow_sanitary_processing"] is True
    assert created["front_side"]["evacuation"]["evacuation_destination"] == "Role 2"
    assert created["front_side"]["body_diagram"]["placeholder_model"] == "TODO:graphic-model-pending"
    assert len(created["back_side"]["stage_log"]) == 2

    # Legacy compatibility fields are auto-derived from canonical payload.
    assert created["injury_mechanism"] == "BLAST"
    assert created["injury_location"] == "Left thigh"
    assert created["documented_by"] == "Medic-Canonical"

    update_resp = await client.patch(
        f"/api/v1/cases/{case_id}/form100",
        json={
            "back_side": {
                "stage_log": [
                    {
                        "arrived_at": datetime(2026, 3, 21, 11, 0, tzinfo=timezone.utc).isoformat(),
                        "stage_name": "ROLE_3",
                        "physician_notes": "Transfer complete",
                        "result": "handoff",
                    },
                    {
                        "arrived_at": datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc).isoformat(),
                        "stage_name": "ROLE_4",
                        "physician_notes": "Definitive care",
                        "result": "admitted",
                    },
                ]
            },
            "front_side": {
                "triage_markers": {
                    "red_urgent_care": True,
                    "yellow_sanitary_processing": False,
                    "black_isolation": True,
                    "blue_radiation_measures": True,
                },
                "evacuation": {
                    "evacuation_transport": "GROUND",
                    "evacuation_destination": "Role 3",
                    "evacuation_priority": "priority",
                    "recommendation_notes": "Ground transfer",
                },
            },
        },
    )
    assert update_resp.status_code == 200

    read_resp = await client.get(f"/api/v1/cases/{case_id}/form100")
    assert read_resp.status_code == 200
    read_data = read_resp.json()["data"]

    assert len(read_data["back_side"]["stage_log"]) == 2
    assert read_data["back_side"]["stage_log"][0]["stage_name"] == "ROLE_3"
    assert read_data["front_side"]["triage_markers"]["black_isolation"] is True
    assert read_data["front_side"]["triage_markers"]["blue_radiation_measures"] is True
    assert read_data["front_side"]["evacuation"]["evacuation_destination"] == "Role 3"
    assert read_data["evacuation_recommendation"] == "Ground transfer"

    case_resp = await client.get(f"/api/v1/cases/{case_id}")
    assert case_resp.status_code == 200
    case_form100 = case_resp.json()["data"]["form100"]
    assert case_form100 is not None
    assert case_form100["front_side"]["triage_markers"]["black_isolation"] is True
    assert case_form100["back_side"]["stage_log"][1]["stage_name"] == "ROLE_4"
