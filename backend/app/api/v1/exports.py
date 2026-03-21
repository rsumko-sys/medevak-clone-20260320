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
from app.models.form100 import Form100Record
from app.models.march import MarchAssessment
from app.models.medications import MedicationAdministration as CaseMedicationAdministration
from app.models.vitals import VitalsObservation as CaseObservation
from app.models.procedures import Procedure as CaseProcedure

from app.repositories.medications import MedicationRepository
from app.repositories.observations import ObservationRepository
from app.repositories.procedures import ProcedureRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def _from_json(value: str | None):
    if not value:
        return None
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def _legacy_to_canonical(form: Form100Record) -> dict:
    marks = []
    if form.injury_location:
        marks.append({"wound_mark_location": form.injury_location})
    return {
        "stub": {
            "issued_at": form.created_at.isoformat() if form.created_at else None,
            "isolation_flag": False,
            "urgent_care_flag": False,
            "sanitary_processing_flag": False,
        },
        "front_side": {
            "injury": {
                "injury_or_illness_datetime": form.injury_datetime.isoformat() if form.injury_datetime else None,
                "diagnosis": form.diagnosis_summary,
                "injury_mechanism": form.injury_mechanism,
                "injury_category_codes": [form.injury_mechanism] if form.injury_mechanism else [],
                "body_diagram_marks": marks,
            },
            "treatment": {
                "treatment_notes": form.treatment_summary,
            },
            "evacuation": {
                "recommendation_notes": form.evacuation_recommendation,
            },
        },
        "back_side": {
            "stage_log": [],
            "signature": {
                "physician_name": form.documented_by,
                "signed_at": form.updated_at.isoformat() if form.updated_at else None,
            },
        },
        "meta_legal_rules": {
            "commander_notified": form.commander_notified,
            "additional_notes": form.notes,
        },
    }


def _canonical_from_form(form: Form100Record) -> dict:
    front_side = {}
    identity = _from_json(form.front_side_identity_json)
    injury = _from_json(form.front_side_injury_json)
    treatment = _from_json(form.front_side_treatment_json)
    evacuation = _from_json(form.front_side_evacuation_json)
    triage_markers = _from_json(form.front_side_triage_markers_json)
    body_diagram = _from_json(form.front_side_body_diagram_json)

    if identity is not None:
        front_side["identity"] = identity
    if injury is not None:
        front_side["injury"] = injury
    if treatment is not None:
        front_side["treatment"] = treatment
    if evacuation is not None:
        front_side["evacuation"] = evacuation
    if triage_markers is not None:
        front_side["triage_markers"] = triage_markers
    if body_diagram is not None:
        front_side["body_diagram"] = body_diagram

    back_side = {}
    stage_log = _from_json(form.back_side_stage_log_json)
    signature = _from_json(form.back_side_signature_json)
    if stage_log is not None:
        back_side["stage_log"] = stage_log
    if signature is not None:
        back_side["signature"] = signature

    canonical = {
        "stub": _from_json(form.stub_json),
        "front_side": front_side if front_side else None,
        "back_side": back_side if back_side else None,
        "meta_legal_rules": _from_json(form.meta_legal_rules_json),
    }
    if not canonical["stub"] and not canonical["front_side"] and not canonical["back_side"] and not canonical["meta_legal_rules"]:
        return _legacy_to_canonical(form)
    return canonical


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
    form_stmt = (
        select(Form100Record)
        .where(Form100Record.case_id == case_id, Form100Record.voided == False)
        .order_by(Form100Record.created_at.desc())
        .limit(1)
    )
    latest_form100 = (await session.execute(form_stmt)).scalars().first()
    canonical_form100 = _canonical_from_form(latest_form100) if latest_form100 else {}

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
        "form_100": {
            "id": getattr(latest_form100, "id", None),
            "document_number": getattr(latest_form100, "document_number", None),
            "injury_datetime": latest_form100.injury_datetime.isoformat() if getattr(latest_form100, "injury_datetime", None) else None,
            "injury_location": getattr(latest_form100, "injury_location", None),
            "injury_mechanism": getattr(latest_form100, "injury_mechanism", None),
            "diagnosis_summary": getattr(latest_form100, "diagnosis_summary", None),
            "documented_by": getattr(latest_form100, "documented_by", None),
            "treatment_summary": getattr(latest_form100, "treatment_summary", None),
            "evacuation_recommendation": getattr(latest_form100, "evacuation_recommendation", None),
            "commander_notified": getattr(latest_form100, "commander_notified", None),
            "notes": getattr(latest_form100, "notes", None),
            "stub": canonical_form100.get("stub"),
            "front_side": canonical_form100.get("front_side"),
            "back_side": canonical_form100.get("back_side"),
            "meta_legal_rules": canonical_form100.get("meta_legal_rules"),
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
