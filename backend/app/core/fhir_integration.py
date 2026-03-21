"""
FHIR Integration Module for MEDEVAK
Integrates fhir.resources for standardized healthcare data exchange
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4

try:
    from fhir.resources.patient import Patient
    from fhir.resources.encounter import Encounter
    from fhir.resources.observation import Observation
    from fhir.resources.medicationadministration import MedicationAdministration as FHIRMedicationAdministration
    from fhir.resources.procedure import Procedure as FHIRProcedure
    from fhir.resources.condition import Condition
    from fhir.resources.bundle import Bundle, BundleEntry
    from fhir.resources.humanname import HumanName
    from fhir.resources.identifier import Identifier
    from fhir.resources.codeableconcept import CodeableConcept
    from fhir.resources.coding import Coding
    from fhir.resources.reference import Reference
    FHIR_AVAILABLE = True
except ImportError:
    print("FHIR resources not available. Install with: pip install fhir.resources")
    FHIR_AVAILABLE = False

from app.models.cases import Case
from app.models.injuries import Injury
from app.models.medications import MedicationAdministration as DbMedicationAdministration
from app.models.procedures import Procedure as DbProcedure
from app.models.vitals import VitalsObservation


class FHIRMapper:
    """Maps MEDEVAK case data to FHIR resources"""
    
    # Triage code mapping to FHIR urgency
    TRIAGE_MAPPING = {
        "!": {"code": "stat", "display": "Immediate - Life Threatening"},
        "+": {"code": "urgent", "display": "Expectant - Expected to Die"},
        "300": {"code": "urgent", "display": "Delayed - Serious"},
        "400": {"code": "asap", "display": "Minimal - Minor"},
        "200": {"code": "asap", "display": "Deceased"}
    }
    
    # Body part mapping (simplified)
    BODY_PART_MAPPING = {
        "HEAD": "71897000",  # Head structure
        "CHEST": "30251500",  # Chest wall structure
        "ABDOMEN": "81608000", # Abdomen structure
        "EXTREMITY": "67826004" # Extremity structure
    }

    # Canonical FHIR observation codings for core Form 100 vitals.
    VITALS_LOINC = {
        "heart_rate": ("8867-4", "Heart rate", "/min"),
        "respiratory_rate": ("9279-1", "Respiratory rate", "/min"),
        "systolic_bp": ("8480-6", "Systolic blood pressure", "mm[Hg]"),
        "diastolic_bp": ("8462-4", "Diastolic blood pressure", "mm[Hg]"),
        "spo2_percent": ("59408-5", "Oxygen saturation in Arterial blood by Pulse oximetry", "%"),
        "temperature_celsius": ("8310-5", "Body temperature", "Cel"),
        "gcs_total": ("9269-2", "Glasgow coma score total", "{score}"),
        "pain_score": ("72514-3", "Pain severity - 0-10 verbal numeric rating", "{score}"),
    }
    
    @classmethod
    def case_to_patient(cls, case: Case) -> Optional[Patient]:
        """Convert Case to FHIR Patient resource"""
        if not FHIR_AVAILABLE:
            return None
            
        patient = Patient(
            id=case.id,
            identifier=[
                Identifier(
                    system="https://medevak.mil/patient-id",
                    value=case.id
                )
            ]
        )
        
        # Name (callsign as primary, full name as secondary)
        if case.callsign:
            given_names = [case.full_name] if case.full_name else None
            patient.name = [
                HumanName(
                    use="usual",
                    family=case.callsign,
                    given=given_names,
                )
            ]
        elif case.full_name:
            patient.name = [
                HumanName(
                    use="official",
                    family=case.full_name.split()[-1] if " " in case.full_name else case.full_name,
                    given=case.full_name.split()[:-1] if " " in case.full_name else []
                )
            ]
        
        # Basic demographics
        if case.blood_type:
            # Add blood type as an extension
            pass
            
        return patient
    
    @classmethod
    def case_to_encounter(cls, case: Case) -> Optional[Encounter]:
        """Convert Case to FHIR Encounter resource"""
        if not FHIR_AVAILABLE:
            return None
            
        encounter = Encounter(
            id=f"encounter-{case.id}",
            status="finished",
            class_fhir=[
                CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                            code="EMER",
                            display="Emergency"
                        )
                    ]
                )
            ],
            subject=Reference(reference=f"Patient/{case.id}")
        )
        
        # Set priority based on triage
        if case.triage_code and case.triage_code in cls.TRIAGE_MAPPING:
            triage = cls.TRIAGE_MAPPING[case.triage_code]
            encounter.priority = CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/v3-ActPriority",
                        code=triage["code"],
                        display=triage["display"]
                    )
                ]
            )
        
        # Incident details
        if case.incident_time:
            try:
                incident_dt = datetime.fromisoformat(case.incident_time.replace('Z', '+00:00'))
                encounter.period.start = incident_dt
            except:
                pass
                
        if case.incident_location:
            encounter.location = [
                Reference(
                    display=case.incident_location
                )
            ]
        
        return encounter
    
    @classmethod
    def injuries_to_conditions(cls, injuries: List[Injury]) -> List[Condition]:
        """Convert injuries to FHIR Condition resources"""
        if not FHIR_AVAILABLE:
            return []
            
        conditions = []
        for injury in injuries:
            condition = Condition(
                id=f"condition-{injury.id}",
                subject=Reference(reference=f"Patient/{injury.case_id}"),
                verificationStatus="confirmed",
                category=[
                    CodeableConcept(
                        coding=[
                            Coding(
                                system="http://terminology.hl7.org/CodeSystem/condition-category",
                                code="injury",
                                display="Injury"
                            )
                        ]
                    )
                ]
            )
            
            # Body structure coding
            if injury.body_region and injury.body_region in cls.BODY_PART_MAPPING:
                condition.bodySite = [
                    CodeableConcept(
                        coding=[
                            Coding(
                                system="http://snomed.info/sct",
                                code=cls.BODY_PART_MAPPING[injury.body_region],
                                display=injury.body_region
                            )
                        ]
                    )
                ]
            
            conditions.append(condition)
        
        return conditions
    
    @classmethod
    def observations_to_observations(cls, observations: List[VitalsObservation]) -> List[Observation]:
        """Convert observations to FHIR Observation resources"""
        if not FHIR_AVAILABLE:
            return []
            
        fhir_observations = []
        
        for obs in observations:
            measured_at = obs.measured_at.isoformat() if obs.measured_at else None
            for field, (loinc_code, display, ucum_unit) in cls.VITALS_LOINC.items():
                value = getattr(obs, field, None)
                if value is None:
                    continue
                fhir_obs_id = f"observation-{obs.id}-{field}".replace("_", "-")

                observation = Observation(
                    id=fhir_obs_id,
                    status="final",
                    subject=Reference(reference=f"Patient/{obs.case_id}"),
                    code=CodeableConcept(
                        coding=[
                            Coding(
                                system="http://loinc.org",
                                code=loinc_code,
                                display=display,
                            )
                        ]
                    ),
                    valueQuantity={
                        "value": float(value),
                        "unit": ucum_unit,
                        "system": "http://unitsofmeasure.org",
                        "code": ucum_unit,
                    },
                )
                if measured_at:
                    observation.effectiveDateTime = measured_at
                fhir_observations.append(observation)

            if obs.avpu:
                avpu_observation = Observation(
                    id=f"observation-{obs.id}-avpu".replace("_", "-"),
                    status="final",
                    subject=Reference(reference=f"Patient/{obs.case_id}"),
                    code=CodeableConcept(
                        coding=[
                            Coding(
                                system="urn:medevak:observation-code",
                                code="avpu",
                                display="AVPU consciousness scale",
                            )
                        ]
                    ),
                    valueString=obs.avpu,
                )
                if measured_at:
                    avpu_observation.effectiveDateTime = measured_at
                fhir_observations.append(avpu_observation)
        
        return fhir_observations
    
    @classmethod
    def medications_to_administrations(cls, medications: List[DbMedicationAdministration]) -> List[FHIRMedicationAdministration]:
        """Convert medications to FHIR MedicationAdministration resources"""
        if not FHIR_AVAILABLE:
            return []
            
        administrations = []
        
        for med in medications:
            administration = FHIRMedicationAdministration(
                id=f"med-admin-{med.id}",
                status="completed",
                subject=Reference(reference=f"Patient/{med.case_id}")
            )
            
            # Medication reference
            administration.medication = CodeableConcept(
                text=med.medication_code
            )
            
            # Dosage
            if med.dose_value:
                administration.dose = {
                    "value": float(med.dose_value) if med.dose_value.replace('.', '').isdigit() else med.dose_value,
                    "unit": med.dose_unit_code or "mg"
                }
            
            # Timing
            if med.time_administered:
                administration.effectiveDateTime = med.time_administered.isoformat()
            
            administrations.append(administration)
        
        return administrations
    
    @classmethod
    def procedures_to_procedures(cls, procedures: List[DbProcedure]) -> List[FHIRProcedure]:
        """Convert procedures to FHIR Procedure resources"""
        if not FHIR_AVAILABLE:
            return []
            
        fhir_procedures = []
        
        for proc in procedures:
            procedure = FHIRProcedure(
                id=f"procedure-{proc.id}",
                status="completed",
                subject=Reference(reference=f"Patient/{proc.case_id}")
            )
            
            procedure.code = CodeableConcept(
                text=proc.procedure_code
            )
            
            if proc.notes:
                procedure.note = [{"text": proc.notes}]
            
            fhir_procedures.append(procedure)
        
        return fhir_procedures
    
    @classmethod
    def create_fhir_bundle(cls, case: Case, injuries: Optional[List[Injury]] = None, 
                          observations: Optional[List[VitalsObservation]] = None,
                          medications: Optional[List[DbMedicationAdministration]] = None,
                          procedures: Optional[List[DbProcedure]] = None) -> Optional[Bundle]:
        """Create a complete FHIR Bundle from case data"""
        if not FHIR_AVAILABLE:
            return None
            
        bundle = Bundle(
            id=f"bundle-{case.id}-{uuid4()}",
            type="collection",
            timestamp=datetime.now(timezone.utc)
        )
        
        entries = []
        
        patient = cls.case_to_patient(case)
        if patient:
            entries.append(BundleEntry(fullUrl=f"urn:uuid:{patient.id}", resource=patient))
        
        encounter = cls.case_to_encounter(case)
        if encounter:
            entries.append(BundleEntry(fullUrl=f"urn:uuid:{encounter.id}", resource=encounter))
        
        if injuries:
            conditions = cls.injuries_to_conditions(injuries)
            for condition in conditions:
                entries.append(BundleEntry(fullUrl=f"urn:uuid:{condition.id}", resource=condition))
        
        if observations:
            fhir_obs = cls.observations_to_observations(observations)
            for obs in fhir_obs:
                entries.append(BundleEntry(fullUrl=f"urn:uuid:{obs.id}", resource=obs))
        
        if medications:
            med_admins = cls.medications_to_administrations(medications)
            for med in med_admins:
                entries.append(BundleEntry(fullUrl=f"urn:uuid:{med.id}", resource=med))
        
        if procedures:
            procs = cls.procedures_to_procedures(procedures)
            for proc in procs:
                entries.append(BundleEntry(fullUrl=f"urn:uuid:{proc.id}", resource=proc))
        
        bundle.entry = entries
        return bundle


def export_case_to_fhir_bundle(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export case data to FHIR Bundle format.
    Returns JSON-serializable dictionary.
    """
    if not FHIR_AVAILABLE:
        return {
            "resourceType": "Bundle",
            "id": f"bundle-{case_data.get('id', 'unknown')}",
            "type": "collection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry": [],
            "error": "FHIR resources not available"
        }

    # Create a mock Case object from dict for the mapper
    # In a real app, we'd fetch the model, but here we can duck-type or convert
    from app.models.cases import Case as CaseModel
    
    case = CaseModel(
        id=case_data.get("id"),
        callsign=case_data.get("callsign"),
        full_name=case_data.get("full_name"),
        triage_code=case_data.get("triage_code"),
        mechanism_of_injury=case_data.get("mechanism_of_injury"),
        incident_time=case_data.get("incident_time"),
        incident_location=case_data.get("incident_location")
    )

    bundle = FHIRMapper.create_fhir_bundle(case=case)
    if bundle:
        return bundle.dict(exclude_none=True)
    
    return {
        "resourceType": "Bundle",
        "entry": []
    }
