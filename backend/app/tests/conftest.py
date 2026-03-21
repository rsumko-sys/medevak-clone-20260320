"""Pytest fixtures — minimal stub."""
import pytest


@pytest.fixture
def sample_case():
    """Sample case for tests."""
    return {
        "id": "test-1",
        "case_number": "100-001",
        "callsign": "VIKING-11",
        "unit": "A-COMPANY",
        "triage_code": "IMMEDIATE",
        "mechanism_of_injury": "BLAST",
        "notes": "Tourniquet applied",
        "observations": [
            {
                "id": "obs-1",
                "observation_type": "HR",
                "value": "112",
                "heart_rate": 112,
                "respiratory_rate": 24,
                "systolic_bp": 90,
                "diastolic_bp": 55,
                "spo2_percent": 92,
                "temperature_celsius": 36.4,
            }
        ],
        "medications": [{"id": "med-1", "medication_code": "TXA", "dose_value": "1", "dose_unit_code": "g"}],
        "procedures": [{"id": "proc-1", "procedure_code": "TOURNIQUET", "notes": "Left thigh"}],
        "created_at": "2025-01-01T00:00:00",
    }
