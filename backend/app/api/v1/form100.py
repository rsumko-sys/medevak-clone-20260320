"""Form 100 router."""
import json
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_request_id, get_session, require_permission
from app.core.security import Permission, SecurityContext
from app.core.utils import envelope
from app.models.cases import Case
from app.models.form100 import Form100Record
from app.schemas.unified import Form100Create, Form100Response, Form100Update


router = APIRouter(prefix="/cases", tags=["form100"])

LEGACY_FIELDS = {
    "document_number",
    "injury_datetime",
    "injury_location",
    "injury_mechanism",
    "diagnosis_summary",
    "documented_by",
    "treatment_summary",
    "evacuation_recommendation",
    "commander_notified",
    "notes",
}


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported type for JSON serialization: {type(value)}")


def _to_json(value):
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _from_json(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def _parse_dt(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _legacy_to_canonical(form: Form100Record) -> dict:
    body_marks = []
    if form.injury_location:
        body_marks.append({"wound_mark_location": form.injury_location})

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
                "body_diagram_marks": body_marks,
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


def _canonical_from_record(form: Form100Record) -> dict:
    canonical = {
        "stub": _from_json(form.stub_json),
        "front_side": {},
        "back_side": {},
        "meta_legal_rules": _from_json(form.meta_legal_rules_json),
    }

    front_side = {}
    if _from_json(form.front_side_identity_json) is not None:
        front_side["identity"] = _from_json(form.front_side_identity_json)
    if _from_json(form.front_side_injury_json) is not None:
        front_side["injury"] = _from_json(form.front_side_injury_json)
    if _from_json(form.front_side_treatment_json) is not None:
        front_side["treatment"] = _from_json(form.front_side_treatment_json)
    if _from_json(form.front_side_evacuation_json) is not None:
        front_side["evacuation"] = _from_json(form.front_side_evacuation_json)
    if _from_json(form.front_side_triage_markers_json) is not None:
        front_side["triage_markers"] = _from_json(form.front_side_triage_markers_json)
    if _from_json(form.front_side_body_diagram_json) is not None:
        front_side["body_diagram"] = _from_json(form.front_side_body_diagram_json)
    canonical["front_side"] = front_side if front_side else None

    back_side = {}
    if _from_json(form.back_side_stage_log_json) is not None:
        back_side["stage_log"] = _from_json(form.back_side_stage_log_json)
    if _from_json(form.back_side_signature_json) is not None:
        back_side["signature"] = _from_json(form.back_side_signature_json)
    canonical["back_side"] = back_side if back_side else None

    if not canonical.get("stub") and not canonical.get("front_side") and not canonical.get("back_side") and not canonical.get("meta_legal_rules"):
        return _legacy_to_canonical(form)
    return canonical


def _merge_canonical(canonical: dict, payload: dict) -> dict:
    out = {
        "stub": canonical.get("stub"),
        "front_side": canonical.get("front_side") or {},
        "back_side": canonical.get("back_side") or {},
        "meta_legal_rules": canonical.get("meta_legal_rules"),
    }

    if "stub" in payload:
        out["stub"] = payload.get("stub")
    if "front_side" in payload:
        out["front_side"] = payload.get("front_side") or {}
    if "back_side" in payload:
        out["back_side"] = payload.get("back_side") or {}
    if "meta_legal_rules" in payload:
        out["meta_legal_rules"] = payload.get("meta_legal_rules")

    injury = ((out.get("front_side") or {}).get("injury") or {})
    if payload.get("injury_datetime") is not None:
        injury["injury_or_illness_datetime"] = payload["injury_datetime"]
    if payload.get("diagnosis_summary") is not None:
        injury["diagnosis"] = payload["diagnosis_summary"]
    if payload.get("injury_mechanism") is not None:
        injury["injury_mechanism"] = payload["injury_mechanism"]
        if not injury.get("injury_category_codes"):
            injury["injury_category_codes"] = [payload["injury_mechanism"]]
    if payload.get("injury_location") is not None and not injury.get("body_diagram_marks"):
        injury["body_diagram_marks"] = [{"wound_mark_location": payload["injury_location"]}]
    if injury:
        out.setdefault("front_side", {})["injury"] = injury

    treatment = ((out.get("front_side") or {}).get("treatment") or {})
    if payload.get("treatment_summary") is not None:
        treatment["treatment_notes"] = payload["treatment_summary"]
    if treatment:
        out.setdefault("front_side", {})["treatment"] = treatment

    evacuation = ((out.get("front_side") or {}).get("evacuation") or {})
    if payload.get("evacuation_recommendation") is not None:
        evacuation["recommendation_notes"] = payload["evacuation_recommendation"]
    if evacuation:
        out.setdefault("front_side", {})["evacuation"] = evacuation

    back_side = out.get("back_side") or {}
    signature = back_side.get("signature") or {}
    if payload.get("documented_by") is not None:
        signature["physician_name"] = payload["documented_by"]
    if signature:
        back_side["signature"] = signature
    if back_side:
        out["back_side"] = back_side

    meta = out.get("meta_legal_rules") or {}
    if payload.get("commander_notified") is not None:
        meta["commander_notified"] = payload["commander_notified"]
    if payload.get("notes") is not None:
        meta["additional_notes"] = payload["notes"]
    if meta:
        out["meta_legal_rules"] = meta

    return out


def _sync_legacy_from_canonical(form: Form100Record, canonical: dict) -> None:
    front_side = canonical.get("front_side") or {}
    injury = front_side.get("injury") or {}
    treatment = front_side.get("treatment") or {}
    evacuation = front_side.get("evacuation") or {}
    back_side = canonical.get("back_side") or {}
    signature = back_side.get("signature") or {}
    meta = canonical.get("meta_legal_rules") or {}

    injury_dt = _parse_dt(injury.get("injury_or_illness_datetime"))
    if injury_dt is not None:
        form.injury_datetime = injury_dt

    if injury.get("diagnosis"):
        form.diagnosis_summary = injury.get("diagnosis")

    if injury.get("injury_mechanism"):
        form.injury_mechanism = injury.get("injury_mechanism")

    marks = injury.get("body_diagram_marks") or []
    if marks and isinstance(marks, list):
        first_location = next((m.get("wound_mark_location") for m in marks if isinstance(m, dict) and m.get("wound_mark_location")), None)
        if first_location:
            form.injury_location = first_location

    if treatment.get("treatment_notes"):
        form.treatment_summary = treatment.get("treatment_notes")

    if evacuation.get("recommendation_notes"):
        form.evacuation_recommendation = evacuation.get("recommendation_notes")

    if signature.get("physician_name"):
        form.documented_by = signature.get("physician_name")

    if meta.get("commander_notified") is not None:
        form.commander_notified = bool(meta.get("commander_notified"))
    if meta.get("additional_notes"):
        form.notes = meta.get("additional_notes")


def _apply_canonical_columns(form: Form100Record, canonical: dict) -> None:
    front_side = canonical.get("front_side") or {}
    back_side = canonical.get("back_side") or {}
    form.stub_json = _to_json(canonical.get("stub"))
    form.front_side_identity_json = _to_json(front_side.get("identity"))
    form.front_side_injury_json = _to_json(front_side.get("injury"))
    form.front_side_treatment_json = _to_json(front_side.get("treatment"))
    form.front_side_evacuation_json = _to_json(front_side.get("evacuation"))
    form.front_side_triage_markers_json = _to_json(front_side.get("triage_markers"))
    form.front_side_body_diagram_json = _to_json(front_side.get("body_diagram"))
    form.back_side_stage_log_json = _to_json(back_side.get("stage_log"))
    form.back_side_signature_json = _to_json(back_side.get("signature"))
    form.meta_legal_rules_json = _to_json(canonical.get("meta_legal_rules"))


def _to_response_payload(form: Form100Record) -> dict:
    canonical = _canonical_from_record(form)
    payload = {
        "id": form.id,
        "case_id": form.case_id,
        "document_number": form.document_number,
        "injury_datetime": form.injury_datetime,
        "injury_location": form.injury_location,
        "injury_mechanism": form.injury_mechanism,
        "diagnosis_summary": form.diagnosis_summary,
        "documented_by": form.documented_by,
        "treatment_summary": form.treatment_summary,
        "evacuation_recommendation": form.evacuation_recommendation,
        "commander_notified": form.commander_notified,
        "notes": form.notes,
        "stub": canonical.get("stub"),
        "front_side": canonical.get("front_side"),
        "back_side": canonical.get("back_side"),
        "meta_legal_rules": canonical.get("meta_legal_rules"),
        "created_at": form.created_at,
        "updated_at": form.updated_at,
        "voided": form.voided,
    }
    return Form100Response.model_validate(payload).model_dump(mode="json")


@router.post("/{case_id}/form100", response_model=dict)
async def create_form100(
    case_id: Annotated[str, Path(...)],
    body: Form100Create,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.CREATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    existing = (
        await session.execute(
            select(Form100Record)
            .where(Form100Record.case_id == case_id, Form100Record.voided == False)
            .order_by(Form100Record.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="Form 100 already exists for this case")

    payload = body.model_dump(exclude_unset=True, mode="python")
    form = Form100Record(
        id=str(uuid.uuid4()),
        case_id=case_id,
        document_number=body.document_number,
        injury_datetime=body.injury_datetime,
        injury_location=body.injury_location,
        injury_mechanism=body.injury_mechanism,
        diagnosis_summary=body.diagnosis_summary,
        documented_by=body.documented_by,
        treatment_summary=body.treatment_summary,
        evacuation_recommendation=body.evacuation_recommendation,
        commander_notified=body.commander_notified,
        notes=body.notes,
    )
    canonical = _merge_canonical(_legacy_to_canonical(form), payload)
    _sync_legacy_from_canonical(form, canonical)
    _apply_canonical_columns(form, canonical)
    session.add(form)
    await session.commit()
    await session.refresh(form)

    return envelope(_to_response_payload(form), request_id=request_id)


@router.get("/{case_id}/form100", response_model=dict)
async def get_form100(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.READ_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    form = (
        await session.execute(
            select(Form100Record)
            .where(Form100Record.case_id == case_id, Form100Record.voided == False)
            .order_by(Form100Record.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if not form:
        raise HTTPException(status_code=404, detail="Form 100 not found")

    return envelope(_to_response_payload(form), request_id=request_id)


@router.patch("/{case_id}/form100", response_model=dict)
async def update_form100(
    case_id: Annotated[str, Path(...)],
    body: Form100Update,
    session: Annotated[AsyncSession, Depends(get_session)],
    ctx: Annotated[SecurityContext, Depends(require_permission(Permission.UPDATE_MEDICAL))],
    request_id: Annotated[str, Depends(get_request_id)],
):
    form = (
        await session.execute(
            select(Form100Record)
            .where(Form100Record.case_id == case_id, Form100Record.voided == False)
            .order_by(Form100Record.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if not form:
        raise HTTPException(status_code=404, detail="Form 100 not found")

    payload = body.model_dump(exclude_unset=True, mode="python")
    for field in LEGACY_FIELDS:
        if field in payload:
            setattr(form, field, payload[field])

    canonical = _merge_canonical(_canonical_from_record(form), payload)
    _sync_legacy_from_canonical(form, canonical)
    _apply_canonical_columns(form, canonical)

    await session.commit()
    await session.refresh(form)
    return envelope(_to_response_payload(form), request_id=request_id)
