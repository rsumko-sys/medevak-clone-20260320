"""Exports router — FHIR, PDF, QR from case data."""
import io
import json
import zipfile
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import Response

from app.api.deps import get_current_user, get_request_id, get_session
from app.core.utils import envelope
from app.exporters.fhir_exporter import export_case_to_fhir
from app.exporters.pdf_exporter import export_case_to_pdf
from app.exporters.qr_exporter import export_case_to_qr
from app.models.cases import Case
from app.models.march import MarchAssessment
from app.models.medications import MedicationAdministration as CaseMedicationAdministration
from app.models.vitals import VitalsObservation as CaseObservation
from app.models.procedures import Procedure as CaseProcedure

from app.repositories.medications import MedicationRepository
from app.repositories.observations import ObservationRepository
from app.repositories.procedures import ProcedureRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _get_case_dict(session: AsyncSession, case_id: str) -> dict | None:
    """Fetch case with observations, medications, procedures as dict."""
    case = await session.get(Case, case_id)
    if not case:
        return None
    obs_repo = ObservationRepository(session)
    med_repo = MedicationRepository(session)
    proc_repo = ProcedureRepository(session)
    obs_list = await obs_repo.get_by_case(case_id)
    meds = await med_repo.get_all(filters=[CaseMedicationAdministration.case_id == case_id])
    procs = await proc_repo.get_all(filters=[CaseProcedure.case_id == case_id])
    march_stmt = (
        select(MarchAssessment)
        .where(MarchAssessment.case_id == case_id, MarchAssessment.voided == False)
        .order_by(MarchAssessment.assessed_at.desc())
        .limit(1)
    )
    latest_march = (await session.execute(march_stmt)).scalars().first()

    def _obs(o):
        return {"id": str(o.id), "case_id": str(o.case_id), "observation_type": o.observation_type, "value": o.value}

    def _med(m):
        t = getattr(m, "time_administered", None)
        return {
            "id": str(m.id), "case_id": str(m.case_id), "medication_code": m.medication_code,
            "dose_value": m.dose_value, "dose_unit_code": m.dose_unit_code,
            "administered_at": t.isoformat() if t else None,
        }

    def _proc(p):
        return {"id": str(p.id), "case_id": str(p.case_id), "procedure_code": p.procedure_code, "notes": p.notes}

    return {
        "id": case.id,
        "mechanism_of_injury": case.mechanism_of_injury,
        "mechanism": case.mechanism,
        "notes": case.notes,
        "triage_code": getattr(case, "triage_code", None),
        "march_notes": {
            "m_notes": getattr(latest_march, "m_notes", None),
            "a_notes": getattr(latest_march, "a_notes", None),
            "r_notes": getattr(latest_march, "r_notes", None),
            "c_notes": getattr(latest_march, "c_notes", None),
            "h_notes": getattr(latest_march, "h_notes", None),
        },
        "observations": [_obs(o) for o in obs_list],
        "medications": [_med(m) for m in meds],
        "procedures": [_proc(p) for p in procs],
    }


router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/{case_id}/fhir")
async def export_fhir(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Export case as FHIR Bundle."""
    case_dict = await _get_case_dict(session, case_id)
    if not case_dict:
        raise HTTPException(status_code=404, detail="Case not found")
    bundle = export_case_to_fhir(case_dict)
    return envelope(bundle, request_id=request_id)


@router.get("/{case_id}/pdf")
async def export_pdf(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
):
    """Export case as PDF file."""
    case_dict = await _get_case_dict(session, case_id)
    if not case_dict:
        raise HTTPException(status_code=404, detail="Case not found")
    pdf_bytes = export_case_to_pdf(case_dict)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="case_{case_id}.pdf"'},
    )


@router.get("/{case_id}/qr")
async def export_qr(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Export case as QR-encodable string."""
    case_dict = await _get_case_dict(session, case_id)
    if not case_dict:
        raise HTTPException(status_code=404, detail="Case not found")
    payload = export_case_to_qr(case_dict)
    return envelope({"data": payload}, request_id=request_id)


@router.get("/{case_id}/bundle")
async def export_bundle(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
):
    """Export compact ZIP bundle for exchange: case JSON, FHIR JSON, QR text, and PDF."""
    case_dict = await _get_case_dict(session, case_id)
    if not case_dict:
        raise HTTPException(status_code=404, detail="Case not found")

    fhir_bundle = export_case_to_fhir(case_dict)
    qr_payload = export_case_to_qr(case_dict)
    pdf_bytes = export_case_to_pdf(case_dict)

    memory = io.BytesIO()
    with zipfile.ZipFile(memory, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps({
            "version": "1.0",
            "case_id": case_id,
            "files": ["case.json", "fhir.json", "qr.txt", "case.pdf"],
        }, ensure_ascii=False, indent=2))
        zf.writestr("case.json", json.dumps(case_dict, ensure_ascii=False, indent=2, default=str))
        zf.writestr("fhir.json", json.dumps(fhir_bundle, ensure_ascii=False, indent=2, default=str))
        zf.writestr("qr.txt", qr_payload)
        zf.writestr("case.pdf", pdf_bytes)

    return Response(
        content=memory.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="case_{case_id}_bundle.zip"'},
    )
