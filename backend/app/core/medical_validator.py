"""
Medical Data Validation Module for MEDEVAK
Integrates medical data validation with HIPAA/GDPR compliance
"""
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    # Try to import medical validation libraries
    import phonenumbers
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False

class ValidationSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    severity: ValidationSeverity
    field: str
    message: str
    code: Optional[str] = None
    recommendation: Optional[str] = None

class MedicalDataValidator:
    """Validates medical data according to healthcare standards"""
    
    # Blood type validation
    BLOOD_TYPES = {
        'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-',
        'A', 'B', 'AB', 'O', 'UNKNOWN'
    }
    
    # Triage codes
    TRIAGE_CODES = {'+', '!', '300', '400', '200'}
    
    # Common medication units
    MEDICATION_UNITS = {
        'mg', 'g', 'mcg', 'ml', 'units', 'iu', 'meq',
        'mg/kg', 'mg/m2', 'mcg/kg', 'units/kg'
    }
    
    # Vital signs ranges
    VITAL_RANGES = {
        'HR': (40, 200),      # Heart rate (bpm)
        'PULSE': (40, 200),   # Pulse (bpm)
        'BP_SYSTOLIC': (70, 250),  # Blood pressure systolic
        'BP_DIASTOLIC': (40, 150), # Blood pressure diastolic
        'TEMP': (35.0, 42.0), # Temperature (Celsius)
        'SPO2': (70, 100),   # Oxygen saturation (%)
        'RR': (8, 40)        # Respiratory rate (breaths/min)
    }
    
    def __init__(self):
        self.validation_rules = {
            'patient_identity': self._validate_patient_identity,
            'triage': self._validate_triage,
            'vitals': self._validate_vitals,
            'medications': self._validate_medications,
            'procedures': self._validate_procedures,
            'incident': self._validate_incident,
            'evacuation': self._validate_evacuation,
            'march': self._validate_march
        }
    
    def validate_case(self, case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate complete case data"""
        results = []
        
        for category, validator in self.validation_rules.items():
            try:
                category_results = validator(case_data)
                results.extend(category_results)
            except Exception as e:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field=category,
                    message=f"Validation error: {str(e)}"
                ))
        
        return results
    
    def _validate_patient_identity(self, case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate patient identity fields"""
        results = []
        
        # Callsign validation
        callsign = case_data.get('callsign', '')
        if callsign:
            if len(callsign) < 2:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field='callsign',
                    message='Callsign too short',
                    recommendation='Callsign should be at least 2 characters'
                ))
            if not re.match(r'^[a-zA-Z0-9\s\-]+$', callsign):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field='callsign',
                    message='Invalid callsign format',
                    recommendation='Use only letters, numbers, spaces, and hyphens'
                ))
        
        # Blood type validation
        blood_type = case_data.get('blood_type', '').upper().strip()
        if blood_type and blood_type not in self.BLOOD_TYPES:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                field='blood_type',
                message=f'Invalid blood type: {blood_type}',
                recommendation=f'Valid types: {", ".join(sorted(self.BLOOD_TYPES))}'
            ))
        
        # Date of birth validation
        dob = case_data.get('dob', '')
        if dob:
            try:
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y%m%d']:
                    try:
                        parsed_date = datetime.strptime(dob, fmt)
                        # Check if date is reasonable (not in future, not too old)
                        now = datetime.now()
                        age = now.year - parsed_date.year
                        if age < 0:
                            results.append(ValidationResult(
                                is_valid=False,
                                severity=ValidationSeverity.ERROR,
                                field='dob',
                                message='Date of birth is in the future'
                            ))
                        elif age > 120:
                            results.append(ValidationResult(
                                is_valid=False,
                                severity=ValidationSeverity.WARNING,
                                field='dob',
                                message='Date of birth indicates very old age',
                                recommendation='Verify date format and accuracy'
                            ))
                        break
                    except ValueError:
                        continue
                else:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        field='dob',
                        message='Invalid date format',
                        recommendation='Use YYYY-MM-DD, DD/MM/YYYY, or YYYYMMDD'
                    ))
            except Exception as e:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field='dob',
                    message=f'Date parsing error: {str(e)}'
                ))
        
        return results
    
    def _validate_triage(self, case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate triage code"""
        results = []
        
        triage_code = case_data.get('triage_code', '').strip()
        if triage_code and triage_code not in self.TRIAGE_CODES:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                field='triage_code',
                message=f'Invalid triage code: {triage_code}',
                recommendation=f'Valid codes: {", ".join(sorted(self.TRIAGE_CODES))}'
            ))
        
        return results
    
    def _validate_vitals(self, case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate vital signs"""
        results = []
        
        vitals_json = case_data.get('vitals_json', [])
        if not isinstance(vitals_json, list):
            return results
        
        for vital in vitals_json:
            if not isinstance(vital, dict):
                continue
                
            obs_type = vital.get('observation_type', '').upper()
            value = vital.get('value', '')
            
            if not obs_type or not value:
                continue
            
            # Try to parse numeric value
            try:
                numeric_value = float(value)
                
                # Check specific vital ranges
                if obs_type in ['HR', 'PULSE']:
                    min_val, max_val = self.VITAL_RANGES['HR']
                    if not (min_val <= numeric_value <= max_val):
                        severity = ValidationSeverity.CRITICAL if numeric_value < 30 or numeric_value > 220 else ValidationSeverity.WARNING
                        results.append(ValidationResult(
                            is_valid=False,
                            severity=severity,
                            field='vitals',
                            message=f'Heart rate {numeric_value} bpm outside normal range ({min_val}-{max_val})',
                            recommendation='Verify measurement accuracy'
                        ))
                
                elif obs_type == 'TEMP':
                    min_val, max_val = self.VITAL_RANGES['TEMP']
                    if not (min_val <= numeric_value <= max_val):
                        severity = ValidationSeverity.CRITICAL if numeric_value < 32 or numeric_value > 43 else ValidationSeverity.WARNING
                        results.append(ValidationResult(
                            is_valid=False,
                            severity=severity,
                            field='vitals',
                            message=f'Temperature {numeric_value}°C outside normal range ({min_val}-{max_val})',
                            recommendation='Check for hypothermia or hyperthermia'
                        ))
                
                elif obs_type == 'SPO2':
                    min_val, max_val = self.VITAL_RANGES['SPO2']
                    if numeric_value < min_val:
                        severity = ValidationSeverity.CRITICAL if numeric_value < 80 else ValidationSeverity.WARNING
                        results.append(ValidationResult(
                            is_valid=False,
                            severity=severity,
                            field='vitals',
                            message=f'Oxygen saturation {numeric_value}% below normal range',
                            recommendation='Consider oxygen supplementation'
                        ))
                
                elif 'BP' in obs_type:
                    # Blood pressure parsing (e.g., "120/80")
                    if '/' in str(value):
                        try:
                            systolic, diastolic = map(float, str(value).split('/'))
                            
                            sys_min, sys_max = self.VITAL_RANGES['BP_SYSTOLIC']
                            dia_min, dia_max = self.VITAL_RANGES['BP_DIASTOLIC']
                            
                            if not (sys_min <= systolic <= sys_max):
                                results.append(ValidationResult(
                                    is_valid=False,
                                    severity=ValidationSeverity.WARNING,
                                    field='vitals',
                                    message=f'Systolic BP {systolic} outside normal range ({sys_min}-{sys_max})'
                                ))
                            
                            if not (dia_min <= diastolic <= dia_max):
                                results.append(ValidationResult(
                                    is_valid=False,
                                    severity=ValidationSeverity.WARNING,
                                    field='vitals',
                                    message=f'Diastolic BP {diastolic} outside normal range ({dia_min}-{dia_max})'
                                ))
                        except ValueError:
                            results.append(ValidationResult(
                                is_valid=False,
                                severity=ValidationSeverity.WARNING,
                                field='vitals',
                                message=f'Invalid blood pressure format: {value}',
                                recommendation='Use format: 120/80'
                            ))
                
            except ValueError:
                # Non-numeric value, check if it's acceptable
                acceptable_non_numeric = ['N/A', 'UNKNOWN', 'CANNOT ASSESS']
                if value.upper() not in acceptable_non_numeric:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.WARNING,
                        field='vitals',
                        message=f'Non-numeric vital sign value: {value}',
                        recommendation='Use numeric values or standard unable-to-assess terms'
                    ))
        
        return results
    
    def _validate_medications(self, case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate medication administrations"""
        results = []
        
        meds_json = case_data.get('medications_json', [])
        if not isinstance(meds_json, list):
            return results
        
        for med in meds_json:
            if not isinstance(med, dict):
                continue
            
            # Check medication name
            med_name = med.get('name', '').strip()
            if not med_name:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field='medications',
                    message='Medication name missing'
                ))
            
            # Check dose
            dose = med.get('dose', '')
            if dose:
                try:
                    # Parse dose value and unit
                    dose_match = re.match(r'^([\d.]+)\s*([a-zA-Z/]+)$', str(dose))
                    if dose_match:
                        dose_value = float(dose_match.group(1))
                        dose_unit = dose_match.group(2).lower()
                        
                        if dose_unit not in self.MEDICATION_UNITS:
                            results.append(ValidationResult(
                                is_valid=False,
                                severity=ValidationSeverity.WARNING,
                                field='medications',
                                message=f'Unusual medication unit: {dose_unit}',
                                recommendation=f'Common units: {", ".join(sorted(self.MEDICATION_UNITS))}'
                            ))
                        
                        # Check for reasonable dose ranges (basic safety check)
                        if dose_value < 0:
                            results.append(ValidationResult(
                                is_valid=False,
                                severity=ValidationSeverity.ERROR,
                                field='medications',
                                message='Negative dose value'
                            ))
                        elif dose_value > 10000:  # Very high dose
                            results.append(ValidationResult(
                                is_valid=False,
                                severity=ValidationSeverity.WARNING,
                                field='medications',
                                message=f'Very high dose: {dose_value} {dose_unit}',
                                recommendation='Verify dose accuracy'
                            ))
                except ValueError:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.WARNING,
                        field='medications',
                        message=f'Invalid dose format: {dose}',
                        recommendation='Use format: "10 mg" or "100 units"'
                    ))
            
            # Check time
            time_admin = med.get('time', '')
            if time_admin:
                try:
                    # Basic time validation
                    if isinstance(time_admin, str):
                        datetime.fromisoformat(time_admin.replace('Z', '+00:00'))
                except ValueError:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.WARNING,
                        field='medications',
                        message=f'Invalid time format: {time_admin}',
                        recommendation='Use ISO format: YYYY-MM-DDTHH:MM:SS'
                    ))
        
        return results
    
    def _validate_procedures(self, case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate procedures"""
        results = []
        
        procedures_json = case_data.get('procedures_json', [])
        if not isinstance(procedures_json, list):
            return results
        
        for proc in procedures_json:
            if not isinstance(proc, dict):
                continue
            
            proc_code = proc.get('code', '').strip()
            if not proc_code:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field='procedures',
                    message='Procedure code missing'
                ))
        
        return results
    
    def _validate_incident(self, case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate incident information"""
        results = []
        
        # Incident time validation
        incident_time = case_data.get('incident_time', '')
        if incident_time:
            try:
                datetime.fromisoformat(incident_time.replace('Z', '+00:00'))
            except ValueError:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field='incident_time',
                    message='Invalid incident time format',
                    recommendation='Use ISO format: YYYY-MM-DDTHH:MM:SS'
                ))
        
        return results
    
    def _validate_evacuation(self, case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate evacuation information"""
        results = []
        
        evac_status = case_data.get('evac_status', '')
        valid_statuses = ['очікує', 'евакуовано', 'загинув', 'в лікарні', 'виписано']
        
        if evac_status and evac_status.lower() not in valid_statuses:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                field='evac_status',
                message=f'Unusual evacuation status: {evac_status}',
                recommendation=f'Common statuses: {", ".join(valid_statuses)}'
            ))
        
        return results
    
    def _validate_march(self, case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate MARCH assessment"""
        results = []
        
        march_fields = ['airway', 'breathing', 'circulation', 'disability', 'exposure']
        
        for field in march_fields:
            value = case_data.get(field, '')
            if value and len(str(value)) > 500:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field=field,
                    message=f'{field} assessment unusually long',
                    recommendation='Consider concise assessment notes'
                ))
        
        return results


# Global validator instance
medical_validator = MedicalDataValidator()


def validate_medical_data(data: Dict[str, Any]) -> Tuple[bool, List[ValidationResult]]:
    """
    Validate medical data and return overall validity with detailed results
    """
    results = medical_validator.validate_case(data)
    
    # Check for any critical or error level issues
    has_critical = any(r.severity == ValidationSeverity.CRITICAL for r in results)
    has_errors = any(r.severity == ValidationSeverity.ERROR for r in results)
    
    is_valid = not (has_critical or has_errors)
    
    return is_valid, results


def get_validation_summary(results: List[ValidationResult]) -> Dict[str, int]:
    """Get summary of validation results by severity"""
    summary = {severity.value: 0 for severity in ValidationSeverity}
    
    for result in results:
        summary[result.severity.value] += 1
    
    return summary
