"""Case to FHIR mapper — maps case data to FHIR R4 resources."""
from typing import Any


def map_case_to_fhir(case: dict[str, Any]) -> dict[str, Any]:
    """Map case dict to FHIR Bundle with Patient, Encounter, Observations, Procedures."""
    case_id = case.get("id", "")
    entries = []

    # Patient
    patient = {
        "resourceType": "Patient",
        "id": case_id,
        "identifier": [{"system": "urn:medevak:case", "value": case_id}],
        "name": [{"text": f"Case {case_id}"}],
    }
    entries.append({"fullUrl": f"urn:uuid:patient-{case_id}", "resource": patient})

    # Encounter
    encounter = {
        "resourceType": "Encounter",
        "id": f"enc-{case_id}",
        "status": "in-progress",
        "subject": {"reference": f"Patient/{case_id}"},
        "reasonCode": [{"text": case.get("mechanism_of_injury") or case.get("mechanism") or ""}],
    }
    if case.get("triage_code"):
        encounter["extension"] = [{"url": "urn:medevak:triage", "valueString": case["triage_code"]}]
    entries.append({"fullUrl": f"urn:uuid:enc-{case_id}", "resource": encounter})

    # Observations
    for obs in case.get("observations") or []:
        o = {
            "resourceType": "Observation",
            "id": obs.get("id", ""),
            "status": "final",
            "subject": {"reference": f"Patient/{case_id}"},
            "code": {"coding": [{"code": obs.get("observation_type", ""), "display": obs.get("observation_type", "")}]},
            "valueString": str(obs.get("value", "")),
        }
        entries.append({"fullUrl": f"urn:uuid:obs-{obs.get('id')}", "resource": o})

    # MedicationAdministration
    for med in case.get("medications") or []:
        m = {
            "resourceType": "MedicationAdministration",
            "id": med.get("id", ""),
            "status": "completed",
            "subject": {"reference": f"Patient/{case_id}"},
            "medicationCodeableConcept": {"coding": [{"code": med.get("medication_code", "")}]},
            "dosage": {"dose": {"value": med.get("dose_value"), "unit": med.get("dose_unit_code", "")}},
        }
        if med.get("administered_at"):
            m["effectiveDateTime"] = med["administered_at"]
        entries.append({"fullUrl": f"urn:uuid:med-{med.get('id')}", "resource": m})

    # Procedure
    for proc in case.get("procedures") or []:
        p = {
            "resourceType": "Procedure",
            "id": proc.get("id", ""),
            "status": "completed",
            "subject": {"reference": f"Patient/{case_id}"},
            "code": {"coding": [{"code": proc.get("procedure_code", ""), "display": proc.get("notes", "")}]},
        }
        entries.append({"fullUrl": f"urn:uuid:proc-{proc.get('id')}", "resource": p})

    return {"resourceType": "Bundle", "type": "document", "entry": entries}
