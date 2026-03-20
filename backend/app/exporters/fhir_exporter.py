"""FHIR exporter — builds FHIR Bundle from case data using fhir.resources."""
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.core.fhir_integration import FHIRMapper, export_case_to_fhir_bundle
from app.models.cases import Case
from app.models.injuries import Injury
from app.models.medications import MedicationAdministration
from app.models.procedures import Procedure
from app.models.vitals import VitalsObservation


def export_case_to_fhir(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export case to FHIR Bundle (Patient, Encounter, Observations, Medications, Procedures).
    Uses fhir.resources for proper FHIR standard compliance.
    
    Args:
        case: Case data dictionary
        
    Returns:
        FHIR Bundle as JSON-serializable dictionary
    """
    return export_case_to_fhir_bundle(case)


def export_case_with_related_data(
    case: Case,
    injuries: Optional[List[Injury]] = None,
    observations: Optional[List[VitalsObservation]] = None,
    medications: Optional[List[MedicationAdministration]] = None,
    procedures: Optional[List[Procedure]] = None
) -> Dict[str, Any]:
    """
    Export complete case with all related data to FHIR Bundle.
    
    Args:
        case: Case model instance
        injuries: List of case injuries
        observations: List of case observations
        medications: List of medication administrations
        procedures: List of procedures
        
    Returns:
        FHIR Bundle as JSON-serializable dictionary
    """
    bundle = FHIRMapper.create_fhir_bundle(
        case=case,
        injuries=injuries or [],
        observations=observations or [],
        medications=medications or [],
        procedures=procedures or []
    )
    
    if bundle is None:
        return {
            "resourceType": "Bundle",
            "id": f"bundle-{case.id}-error",
            "type": "collection",
            "timestamp": datetime.utcnow().isoformat(),
            "entry": [],
            "error": "FHIR resources not available"
        }
    
    return bundle.dict(exclude_none=True)


def validate_fhir_bundle(bundle: Dict[str, Any]) -> List[str]:
    """
    Basic validation of FHIR Bundle structure.
    
    Args:
        bundle: FHIR Bundle dictionary
        
    Returns:
        List of validation errors
    """
    errors = []
    
    if not isinstance(bundle, dict):
        errors.append("Bundle must be a dictionary")
        return errors
    
    if bundle.get("resourceType") != "Bundle":
        errors.append("Missing or incorrect resourceType (should be 'Bundle')")
    
    if bundle.get("type") != "collection":
        errors.append("Bundle type should be 'collection'")
    
    if "entry" not in bundle:
        errors.append("Bundle must have an 'entry' field")
    elif not isinstance(bundle["entry"], list):
        errors.append("Bundle entry must be a list")
    
    return errors


def get_fhir_summary(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract summary information from FHIR Bundle.
    
    Args:
        bundle: FHIR Bundle dictionary
        
    Returns:
        Summary with resource counts and types
    """
    if not isinstance(bundle, dict) or "entry" not in bundle:
        return {"error": "Invalid bundle structure"}
    
    resource_types: Dict[str, int] = {}
    summary = {
        "total_resources": len(bundle["entry"]),
        "resource_types": resource_types,
        "patient_id": None,
        "encounter_id": None
    }
    
    for entry in bundle["entry"]:
        if not isinstance(entry, dict) or "resource" not in entry:
            continue
            
        resource = entry["resource"]
        resource_type = resource.get("resourceType", "Unknown")
        
        if resource_type not in resource_types:
            resource_types[resource_type] = 0
        resource_types[resource_type] += 1
        
        if resource_type == "Patient":
            summary["patient_id"] = resource.get("id")
        elif resource_type == "Encounter":
            summary["encounter_id"] = resource.get("id")
    
    return summary
