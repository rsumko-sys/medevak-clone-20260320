"""API router."""
from fastapi import APIRouter
from app.api.v1 import (
    auth,
    ws,
    handoff,
    cases,
    medications,
    sync,
    audit,
    documents,
    body_markers,
    injuries,
    events,
    evacuation,
    march,
    reference,
    exports,
    vitals,
    procedures,
    transcribe,
    fhir,
    personnel,
    storage,
    settings,
    field_drop,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(ws.router)
api_router.include_router(handoff.router)
api_router.include_router(cases.router)
api_router.include_router(medications.router)
api_router.include_router(sync.router)
api_router.include_router(audit.router)
api_router.include_router(documents.router)
api_router.include_router(body_markers.router)
api_router.include_router(injuries.router)
api_router.include_router(events.router)
api_router.include_router(evacuation.router)
api_router.include_router(march.router)
api_router.include_router(reference.router)
api_router.include_router(exports.router)
api_router.include_router(vitals.router)
api_router.include_router(procedures.router)
api_router.include_router(transcribe.router)
api_router.include_router(fhir.router)
api_router.include_router(personnel.router)
api_router.include_router(storage.router)
api_router.include_router(settings.router)
api_router.include_router(field_drop.router)
