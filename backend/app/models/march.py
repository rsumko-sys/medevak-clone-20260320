"""MARCH Assessments model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text
from app.core.database import Base


class MarchAssessment(Base):
    __tablename__ = "march_assessments"
    
    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    assessed_at = Column(DateTime, default=datetime.utcnow)
    
    # M: Massive Bleeding
    m_massive_bleeding = Column(Boolean, default=False)
    m_tourniquets_applied = Column(Integer, default=0)
    m_hemostatic_agent = Column(Boolean, default=False)
    m_notes = Column(Text, nullable=True)
    
    # A: Airway
    a_airway_open = Column(Boolean, default=False)
    a_airway_intervention = Column(String, nullable=True) # Intact, NPA, SGA, Cric
    a_notes = Column(Text, nullable=True)
    
    # R: Respiration
    r_breathing_rate = Column(Integer, nullable=True)
    r_chest_seal_applied = Column(Boolean, default=False)
    r_needle_d_performed = Column(Boolean, default=False)
    r_chest_tube = Column(Boolean, default=False)
    r_notes = Column(Text, nullable=True)
    
    # C: Circulation
    c_radial_pulse = Column(String, nullable=True) # Absent, Weak, Normal
    c_capillary_refill_time = Column(String, nullable=True) # <2s, >2s
    c_pelvic_binder = Column(Boolean, default=False)
    c_tibial_io = Column(Boolean, default=False)
    c_sternal_io = Column(Boolean, default=False)
    c_iv_access = Column(Boolean, default=False)
    c_notes = Column(Text, nullable=True)
    
    # H: Hypothermia/Head
    h_hypothermia_prevented = Column(Boolean, default=False)
    h_blanket_applied = Column(Boolean, default=False)
    h_active_warming = Column(Boolean, default=False)
    h_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    voided = Column(Boolean, default=False)
