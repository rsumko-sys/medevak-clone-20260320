"""FHIR API endpoints - Export cases to FHIR standard format."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_request_id, get_session
from app.core.utils import envelope
from app.exporters.fhir_exporter import (
    export_case_with_related_data,
    validate_fhir_bundle,
    get_fhir_summary
)
from app.repositories.cases import CasesRepository
from app.repositories.observations import ObservationRepository
from app.repositories.procedures import ProcedureRepository
from app.repositories.medications import MedicationRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["FHIR"])


@router.get("/cases/{case_id}/fhir")
async def export_case_fhir(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Export a case to FHIR Bundle format with all related data."""
    
    # Get case
    cases_repo = CasesRepository(session)
    case = await cases_repo.get_by_id(case_id)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Get related data
    obs_repo = ObservationRepository(session)
    proc_repo = ProcedureRepository(session)
    med_repo = MedicationRepository(session)
    
    observations = await obs_repo.get_by_case(case_id)
    procedures = await proc_repo.get_by_case(case_id)
    medications = await med_repo.get_by_case(case_id)
    
    # Export to FHIR
    try:
        fhir_bundle = export_case_with_related_data(
            case=case,
            observations=observations,
            procedures=procedures,
            medications=medications
        )
        
        # Validate FHIR bundle
        validation_errors = validate_fhir_bundle(fhir_bundle)
        if validation_errors:
            logger.warning(f"FHIR validation errors for case {case_id}: {validation_errors}")
            fhir_bundle["validation_errors"] = validation_errors
        
        # Add summary
        fhir_bundle["summary"] = get_fhir_summary(fhir_bundle)
        
        return envelope(fhir_bundle, request_id=request_id)
        
    except Exception as e:
        logger.error(f"FHIR export failed for case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"FHIR export failed: {str(e)}")


@router.get("/cases/{case_id}/fhir/summary")
async def get_fhir_summary_endpoint(
    case_id: Annotated[str, Path(...)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Get FHIR export summary without full data."""
    
    # Get case
    cases_repo = CasesRepository(session)
    case = await cases_repo.get_by_id(case_id)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Export minimal FHIR data for summary
    try:
        fhir_bundle = export_case_with_related_data(case=case)
        
        if "error" in fhir_bundle:
            raise HTTPException(status_code=500, detail=fhir_bundle["error"])
        
        summary = get_fhir_summary(fhir_bundle)
        summary["case_id"] = case_id
        summary["export_timestamp"] = fhir_bundle.get("timestamp")
        
        return envelope(summary, request_id=request_id)
        
    except Exception as e:
        logger.error(f"FHIR summary failed for case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"FHIR summary failed: {str(e)}")


@router.get("/fhir/status")
async def fhir_status(
    user: Annotated[dict, Depends(get_current_user)],
    request_id: Annotated[str, Depends(get_request_id)],
):
    """Check FHIR integration status and capabilities."""
    
    try:
        from app.core.fhir_integration import FHIR_AVAILABLE
        
        status = {
            "fhir_available": FHIR_AVAILABLE,
            "supported_resources": [
                "Patient",
                "Encounter", 
                "Condition",
                "Observation",
                "MedicationAdministration",
                "Procedure",
                "Bundle"
            ],
            "fhir_version": "R4",
            "export_formats": ["application/fhir+json", "application/json"]
        }
        
        if not FHIR_AVAILABLE:
            status["error"] = "FHIR resources library not installed"
            status["installation_hint"] = "Install with: pip install fhir.resources"
        
        return envelope(status, request_id=request_id)
        
    except Exception as e:
        logger.error(f"FHIR status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"FHIR status check failed: {str(e)}")
