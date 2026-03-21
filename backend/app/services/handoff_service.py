"""Handoff service — persists to DB."""
import uuid
from app.models.evacuation import EvacuationRecord as CaseHandoff

from app.repositories.handoff import HandoffRepository


class HandoffService:
    def __init__(self, session, user_id: str | None = None, device_id: str | None = None):
        self._session = session
        self._handoff_repo = HandoffRepository(session)
        self._user_id = user_id
        self._device_id = device_id

    async def generate(self, case_id: str):
        """Generate or fetch handoff — persists to DB."""
        items = await self._handoff_repo.get_all(
            filters=[CaseHandoff.case_id == case_id],
            order_by=CaseHandoff.created_at.desc(),
            limit=1,
        )
        if items:
            return {"id": items[0].id, "case_id": items[0].case_id, "mist_summary": items[0].mist_summary or ""}
        handoff_id = str(uuid.uuid4())
        handoff = CaseHandoff(
            id=handoff_id,
            case_id=case_id,
            mist_summary="",
        )
        self._session.add(handoff)
        await self._session.commit()
        await self._session.refresh(handoff)
        return {"id": handoff.id, "case_id": handoff.case_id, "mist_summary": handoff.mist_summary or ""}

    async def update(self, case_id: str, body):
        """Update handoff mist_summary — persists to DB."""
        items = await self._handoff_repo.get_all(
            filters=[CaseHandoff.case_id == case_id],
            order_by=CaseHandoff.created_at.desc(),
            limit=1,
        )
        mist = getattr(body, "mist_summary", "") or ""
        if items:
            h = items[0]
            h.mist_summary = mist
            await self._session.commit()
            await self._session.refresh(h)
            return {"id": h.id, "case_id": h.case_id, "mist_summary": h.mist_summary}
        handoff_id = str(uuid.uuid4())
        handoff = CaseHandoff(id=handoff_id, case_id=case_id, mist_summary=mist)
        self._session.add(handoff)
        await self._session.commit()
        await self._session.refresh(handoff)
        return {"id": handoff.id, "case_id": handoff.case_id, "mist_summary": handoff.mist_summary}

    async def confirm(self, case_id: str, body):
        """Confirm handoff — returns existing handoff (confirmation flag could be added to model)."""
        items = await self._handoff_repo.get_all(
            filters=[CaseHandoff.case_id == case_id],
            order_by=CaseHandoff.created_at.desc(),
            limit=1,
        )
        if items:
            return {"id": items[0].id, "case_id": case_id, "confirmed": True}
        return {"case_id": case_id, "confirmed": True}
