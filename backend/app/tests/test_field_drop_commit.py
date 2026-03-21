"""
Integration tests for the field-drop commit endpoint.

SQLite tests:  run always        (in-memory, fast)
Postgres test: run only when PG_TEST_URL env var is set, e.g.:
    PG_TEST_URL=postgresql+asyncpg://user:pass@localhost:5432/testdb pytest -k parallel

To set up a local Postgres container:
    docker run --rm -p 5432:5432 -e POSTGRES_PASSWORD=test -e POSTGRES_DB=testdb postgres:16
    PG_TEST_URL=postgresql+asyncpg://postgres:test@localhost:5432/testdb pytest backend/app/tests/test_field_drop_commit.py
"""
import asyncio
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_session
from app.models.field_drop import (
    FieldDispatchLog,
    FieldInventoryItem,
    FieldPosition,
    FieldSupplyNeed,
    FieldSupplyRequest,
)

# ---------------------------------------------------------------------------
# Ensure ALL models are registered with Base.metadata before create_all()
# ---------------------------------------------------------------------------
import app.models.cases          # noqa: F401
import app.models.audit          # noqa: F401
import app.models.documents      # noqa: F401
import app.models.user           # noqa: F401
import app.models.sync_queue     # noqa: F401
import app.models.march          # noqa: F401
import app.models.injuries       # noqa: F401
import app.models.procedures     # noqa: F401
import app.models.medications    # noqa: F401
import app.models.vitals         # noqa: F401
import app.models.evacuation     # noqa: F401
import app.models.events         # noqa: F401
import app.models.idempotency    # noqa: F401
import app.models.personnel      # noqa: F401


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sqlite_engine():
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )


async def _bootstrap(engine):
    """Create all tables for the given engine."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _seed(session: AsyncSession, *, bandage_qty: int = 10, radius_km: float = 50.0):
    """
    Seed one position with `bandage_qty` bandages and return a request
    that needs 2 of them.
    """
    pos_id = str(uuid.uuid4())
    req_id = str(uuid.uuid4())

    session.add(FieldPosition(id=pos_id, name="Alpha", x=0.0, y=0.0))
    session.add(FieldInventoryItem(
        id=str(uuid.uuid4()), position_id=pos_id, item_name="bandage", qty=bandage_qty
    ))
    session.add(FieldSupplyRequest(
        id=req_id, x=0.5, y=0.5, urgency="high", radius_km=radius_km,
        status="DRAFT", created_by="test-user"
    ))
    session.add(FieldSupplyNeed(
        id=str(uuid.uuid4()), request_id=req_id, item_name="bandage", qty=2
    ))
    await session.commit()
    return pos_id, req_id


def _make_app(engine):
    """Return the FastAPI app with get_session wired to the given engine."""
    from backend.main import app as fastapi_app

    TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_session():
        async with TestSessionLocal() as session:
            yield session

    fastapi_app.dependency_overrides[get_session] = override_get_session
    return fastapi_app


# ---------------------------------------------------------------------------
# SQLite fixtures (auto-use per test for isolation)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    engine = _sqlite_engine()
    await _bootstrap(engine)
    app = _make_app(engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, engine
    await engine.dispose()
    # Clean override so other tests are unaffected
    from backend.main import app as fastapi_app
    fastapi_app.dependency_overrides.pop(get_session, None)


# ---------------------------------------------------------------------------
# Test 1 — fresh commit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fresh_commit(client):
    ac, engine = client
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        _, req_id = await _seed(s)

    r = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/commit",
        headers={"X-User-ID": "test-user", "Idempotency-Key": f"fresh-{uuid.uuid4()}"},
    )
    assert r.status_code == 200
    d = r.json()["data"]

    assert d["request_id"] == req_id
    assert d["already_committed"] is False
    assert d["request_status"] == "DISPATCHED"
    assert d["logs_created"] > 0
    assert d["shortages"] == []
    assert all(row["status"] == "APPLIED" for row in d["applied"])


# ---------------------------------------------------------------------------
# Test 2 — repeat commit with a different idempotency key
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_repeat_commit_new_key(client):
    ac, engine = client
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        _, req_id = await _seed(s)

    key1 = f"k1-{uuid.uuid4()}"
    key2 = f"k2-{uuid.uuid4()}"

    r1 = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/commit",
        headers={"X-User-ID": "test-user", "Idempotency-Key": key1},
    )
    assert r1.status_code == 200
    assert r1.json()["data"]["already_committed"] is False

    r2 = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/commit",
        headers={"X-User-ID": "test-user", "Idempotency-Key": key2},
    )
    assert r2.status_code == 200
    d2 = r2.json()["data"]
    assert d2["already_committed"] is True
    assert d2["applied"] == []
    assert d2["logs_created"] == 0
    assert d2["request_id"] == req_id


# ---------------------------------------------------------------------------
# Test 3 — same idempotency key replay
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_same_key_replay(client):
    ac, engine = client
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        _, req_id = await _seed(s)

    key = f"replay-{uuid.uuid4()}"
    r1 = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/commit",
        headers={"X-User-ID": "test-user", "Idempotency-Key": key},
    )
    r2 = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/commit",
        headers={"X-User-ID": "test-user", "Idempotency-Key": key},
    )
    assert r1.status_code == r2.status_code == 200
    # Same key must return byte-identical body
    assert r1.json()["data"] == r2.json()["data"]


# ---------------------------------------------------------------------------
# Test 4 — partial shortage (want 2, only 1 available)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_partial_shortage(client):
    ac, engine = client
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        pos_id = str(uuid.uuid4())
        req_id = str(uuid.uuid4())
        s.add(FieldPosition(id=pos_id, name="Bravo", x=0.0, y=0.0))
        # Only 1 available, request needs 2
        s.add(FieldInventoryItem(
            id=str(uuid.uuid4()), position_id=pos_id, item_name="bandage", qty=1
        ))
        s.add(FieldSupplyRequest(
            id=req_id, x=0.5, y=0.5, urgency="high", radius_km=50.0,
            status="DRAFT", created_by="test-user"
        ))
        s.add(FieldSupplyNeed(
            id=str(uuid.uuid4()), request_id=req_id, item_name="bandage", qty=2
        ))
        await s.commit()

    r = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/commit",
        headers={"X-User-ID": "test-user", "Idempotency-Key": f"partial-{uuid.uuid4()}"},
    )
    assert r.status_code == 200
    d = r.json()["data"]

    assert d["request_status"] == "PARTIAL"
    assert len(d["shortages"]) > 0
    assert d["shortages"][0]["missing_qty"] == 1
    assert d["shortages"][0]["item_name"] == "bandage"
    # Applied row must carry what was actually sent
    applied = [row for row in d["applied"] if row["status"] == "APPLIED"]
    assert applied[0]["qty"] == 1  # only 1 actually shipped

    # Inventory must be drained to 0, not negative
    from sqlalchemy import select
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        item = (await s.execute(
            select(FieldInventoryItem).where(
                FieldInventoryItem.position_id == pos_id,
                FieldInventoryItem.item_name == "bandage",
            )
        )).scalar_one()
        assert item.qty == 0


# ---------------------------------------------------------------------------
# Test 5 — zero inventory → FAILED, not DISPATCHED
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_zero_inventory_is_failed(client):
    ac, engine = client
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        pos_id = str(uuid.uuid4())
        req_id = str(uuid.uuid4())
        s.add(FieldPosition(id=pos_id, name="Charlie", x=0.0, y=0.0))
        s.add(FieldInventoryItem(
            id=str(uuid.uuid4()), position_id=pos_id, item_name="bandage", qty=0
        ))
        s.add(FieldSupplyRequest(
            id=req_id, x=0.5, y=0.5, urgency="high", radius_km=50.0,
            status="DRAFT", created_by="test-user"
        ))
        s.add(FieldSupplyNeed(
            id=str(uuid.uuid4()), request_id=req_id, item_name="bandage", qty=3
        ))
        await s.commit()

    r = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/commit",
        headers={"X-User-ID": "test-user"},
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["request_status"] == "FAILED"
    assert d["logs_created"] == 0
    assert d["applied"] == [] or all(row["status"] != "APPLIED" for row in d["applied"])


# ---------------------------------------------------------------------------
# Test 6 — finalize after successful commit → COMPLETED
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fresh_finalize(client):
    ac, engine = client
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        _, req_id = await _seed(s)

    # First commit the request
    r1 = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/commit",
        headers={"X-User-ID": "test-user", "Idempotency-Key": f"commit-fin-{uuid.uuid4()}"},
    )
    assert r1.status_code == 200
    prev_status = r1.json()["data"]["request_status"]
    assert prev_status in {"DISPATCHED", "PARTIAL"}

    # Now finalize
    r2 = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/finalize",
        json={"result": "completed", "method": "RADIO", "note": "confirmed by radio"},
        headers={"X-User-ID": "test-user", "Idempotency-Key": f"fin-{uuid.uuid4()}"},
    )
    assert r2.status_code == 200
    d = r2.json()["data"]
    assert d["ok"] is True
    assert d["request_status"] == "COMPLETED"
    assert d["previous_status"] == prev_status
    assert d["method"] == "RADIO"
    assert d["note"] == "confirmed by radio"
    assert d["finalized_by"] is not None  # dev-auth maps to dev-user
    assert d["finalized_at"] is not None


# ---------------------------------------------------------------------------
# Test 7 — repeat finalize (idempotent)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_repeat_finalize(client):
    ac, engine = client
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        _, req_id = await _seed(s)

    # Commit
    await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/commit",
        headers={"X-User-ID": "test-user", "Idempotency-Key": f"c-{uuid.uuid4()}"},
    )

    # Finalize once
    r1 = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/finalize",
        json={"result": "completed", "method": "MANUAL"},
        headers={"X-User-ID": "test-user", "Idempotency-Key": f"fin1-{uuid.uuid4()}"},
    )
    assert r1.json()["data"]["request_status"] == "COMPLETED"

    # Finalize a second time (different key, already COMPLETED) → still ok
    r2 = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/finalize",
        json={"result": "completed", "method": "MANUAL"},
        headers={"X-User-ID": "test-user", "Idempotency-Key": f"fin2-{uuid.uuid4()}"},
    )
    assert r2.status_code == 200
    d2 = r2.json()["data"]
    assert d2["ok"] is True
    assert d2["request_status"] == "COMPLETED"


# ---------------------------------------------------------------------------
# Test 8 — finalize from DRAFT → 409
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_finalize_from_draft_is_rejected(client):
    ac, engine = client
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        _, req_id = await _seed(s)
    # Don't commit — request is still DRAFT
    r = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/finalize",
        json={"result": "completed", "method": "VOICE"},
        headers={"X-User-ID": "test-user"},
    )
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# Test 9 — finalize from FAILED → 409
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_finalize_from_failed_is_rejected(client):
    ac, engine = client
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as s:
        pos_id = str(uuid.uuid4())
        req_id = str(uuid.uuid4())
        s.add(FieldPosition(id=pos_id, name="Echo", x=0.0, y=0.0))
        # Zero stock forces FAILED
        s.add(FieldInventoryItem(
            id=str(uuid.uuid4()), position_id=pos_id, item_name="bandage", qty=0
        ))
        s.add(FieldSupplyRequest(
            id=req_id, x=0.5, y=0.5, urgency="high", radius_km=50.0,
            status="DRAFT", created_by="test-user"
        ))
        s.add(FieldSupplyNeed(
            id=str(uuid.uuid4()), request_id=req_id, item_name="bandage", qty=2
        ))
        await s.commit()

    # Commit → FAILED
    rc = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/commit",
        headers={"X-User-ID": "test-user"},
    )
    assert rc.json()["data"]["request_status"] == "FAILED"

    # Now try to finalize → 409
    r = await ac.post(
        f"/api/v1/field-drop/requests/{req_id}/finalize",
        json={"result": "completed", "method": "DISCORD"},
        headers={"X-User-ID": "test-user"},
    )
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# Test 10 — parallel double commit against Postgres (requires PG_TEST_URL env)
# ---------------------------------------------------------------------------

PG_TEST_URL = os.getenv("PG_TEST_URL")

@pytest.mark.asyncio
@pytest.mark.skipif(not PG_TEST_URL, reason="PG_TEST_URL not set — skipping Postgres parallel test")
async def test_parallel_double_commit_postgres():
    """
    Two different requests each want 2 bandages from the same position (3 total).
    Both commits fire concurrently.
    Expected invariants:
      - inventory never goes below 0
      - sum of all APPLIED qty <= initial stock (3)
      - one request is DISPATCHED, the other is PARTIAL or FAILED
      - we never get two DISPATCHED results claiming the same stock
    """
    assert PG_TEST_URL is not None  # mypy hint

    pg_engine = create_async_engine(PG_TEST_URL, echo=False)
    PGSession = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)

    # Create schema
    async with pg_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Seed: one position, 3 bandages, two requests that each need 2
    pos_id = str(uuid.uuid4())
    req_id_a = str(uuid.uuid4())
    req_id_b = str(uuid.uuid4())
    INITIAL_STOCK = 3

    async with PGSession() as s:
        s.add(FieldPosition(id=pos_id, name="DeltaPG", x=0.0, y=0.0))
        s.add(FieldInventoryItem(
            id=str(uuid.uuid4()), position_id=pos_id, item_name="bandage", qty=INITIAL_STOCK
        ))
        for req_id in (req_id_a, req_id_b):
            s.add(FieldSupplyRequest(
                id=req_id, x=0.5, y=0.5, urgency="high", radius_km=50.0,
                status="DRAFT", created_by="test-user"
            ))
            s.add(FieldSupplyNeed(
                id=str(uuid.uuid4()), request_id=req_id, item_name="bandage", qty=2
            ))
        await s.commit()

    # Override app session with PG session
    from backend.main import app as fastapi_app

    def _override():
        async def _session_gen():
            async with PGSession() as session:
                yield session
        return _session_gen

    fastapi_app.dependency_overrides[get_session] = _override()

    try:
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://test"
        ) as ac:
            results = await asyncio.gather(
                ac.post(
                    f"/api/v1/field-drop/requests/{req_id_a}/commit",
                    headers={"X-User-ID": "test-user", "Idempotency-Key": f"pg-a-{uuid.uuid4()}"},
                ),
                ac.post(
                    f"/api/v1/field-drop/requests/{req_id_b}/commit",
                    headers={"X-User-ID": "test-user", "Idempotency-Key": f"pg-b-{uuid.uuid4()}"},
                ),
                return_exceptions=True,
            )

        statuses = []
        total_applied_qty = 0

        for result in results:
            assert not isinstance(result, Exception), f"Request raised: {result}"
            assert result.status_code == 200
            d = result.json()["data"]
            statuses.append(d["request_status"])
            total_applied_qty += sum(row["qty"] for row in d["applied"] if row["status"] == "APPLIED")

        # Invariant 1: total applied qty never exceeds initial stock
        assert total_applied_qty <= INITIAL_STOCK, (
            f"Stock overcommitted: applied {total_applied_qty} from {INITIAL_STOCK}"
        )

        # Invariant 2: cannot have two DISPATCHED when stock only covers one
        dispatched = statuses.count("DISPATCHED")
        assert dispatched <= 1, f"Both requests became DISPATCHED: {statuses}"

        # Invariant 3: at least one completed something useful
        assert "DISPATCHED" in statuses or "PARTIAL" in statuses, (
            f"Expected at least one DISPATCHED or PARTIAL, got: {statuses}"
        )

        # Invariant 4: DB inventory is not negative
        from sqlalchemy import select
        async with PGSession() as s:
            item = (await s.execute(
                select(FieldInventoryItem).where(
                    FieldInventoryItem.position_id == pos_id,
                    FieldInventoryItem.item_name == "bandage",
                )
            )).scalar_one()
            assert item.qty >= 0, f"Inventory went negative: {item.qty}"
            # Final qty + total applied must equal initial stock
            assert item.qty + total_applied_qty == INITIAL_STOCK, (
                f"Stock not conserved: {item.qty} remaining + {total_applied_qty} applied "
                f"!= {INITIAL_STOCK}"
            )
    finally:
        fastapi_app.dependency_overrides.pop(get_session, None)
        async with pg_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await pg_engine.dispose()
