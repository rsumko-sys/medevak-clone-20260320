"""Personnel records models - військові особові справи."""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean, JSON
from sqlalchemy.dialects.sqlite import JSON
from app.core.database import Base


class ServiceMember(Base):
    """Військовослужбовець - основна модель особової справи."""
    __tablename__ = "service_members"
    
    # Ідентифікація
    id = Column(String, primary_key=True)
    service_number = Column(String, unique=True, nullable=True, index=True)  # Військовий номер
    social_security = Column(String, unique=True, nullable=True, index=True)  # Соціальний номер
    
    # Персональні дані
    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True) 
    middle_name = Column(String, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    place_of_birth = Column(String, nullable=True)
    citizenship = Column(String, nullable=True)
    
    # Військові дані
    rank = Column(String, nullable=True)  # Звання
    specialty = Column(String, nullable=True)  # Військова спеціальність/MOS
    unit = Column(String, nullable=True)  # Підрозділ
    position = Column(String, nullable=True)  # Посада
    
    # Служба
    enlistment_date = Column(DateTime, nullable=True)  # Дата призову/контракту
    service_start_date = Column(DateTime, nullable=True)  # Початок служби
    contract_end_date = Column(DateTime, nullable=True)  # Кінець контракту
    years_of_service = Column(Float, nullable=True)  # Вислуга років
    
    # Контактна інформація
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(JSON, nullable=True)  # Контактна особа
    
    # Медичні дані
    blood_type = Column(String, nullable=True)
    allergies = Column(Text, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    last_physical_date = Column(DateTime, nullable=True)
    
    # Бойовий досвід
    deployments = Column(JSON, nullable=True)  # Список розгортань
    combat_experience = Column(Boolean, default=False)
    awards = Column(JSON, nullable=True)  # Нагороди
    qualifications = Column(JSON, nullable=True)  # Кваліфікації
    
    # Статус
    status = Column(String, default="ACTIVE")  # ACTIVE, INACTIVE, DEPLOYED, MEDICAL_HOLD
    is_deployed = Column(Boolean, default=False)
    
    # Метадані
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    
    # Reliability & Recovery
    is_deleted = Column(Boolean, default=False)
    version_id = Column(Integer, default=1)  # Optimistic locking



class PersonnelRecord(Base):
    """Запис в особовій справі - різні події та документи."""
    __tablename__ = "personnel_records"
    
    id = Column(String, primary_key=True)
    service_member_id = Column(String, ForeignKey("service_members.id"), nullable=False)
    
    # Тип запису
    record_type = Column(String, nullable=False)  # ENLISTMENT, PROMOTION, DEPLOYMENT, INJURY, AWARD, MEDICAL
    
    # Дані запису
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Деталі в JSON форматі
    
    # Дати
    effective_date = Column(DateTime, nullable=True)  # Дата події
    recorded_date = Column(DateTime, default=datetime.utcnow)  # Дата запису
    
    # Пов'язані документи
    document_references = Column(JSON, nullable=True)  # Посилання на документи
    
    # Хто створив
    recorded_by = Column(String, nullable=True)
    authorizing_official = Column(String, nullable=True)
    
    # Статус
    status = Column(String, default="ACTIVE")  # ACTIVE, ARCHIVED, SUPERSEDED
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class MedicalRecord(Base):
    """Медичний запис військовослужбовця."""
    __tablename__ = "medical_records"
    
    id = Column(String, primary_key=True)
    service_member_id = Column(String, ForeignKey("service_members.id"), nullable=False)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True)  # Пов'язаний медичний кейс
    
    # Тип медичного запису
    record_type = Column(String, nullable=False)  # INJURY, TREATMENT, EXAMINATION, VACCINATION
    
    # Медичні дані
    diagnosis = Column(String, nullable=True)
    diagnosis_code = Column(String, nullable=True)  # ICD-10 код
    treatment = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    procedures = Column(Text, nullable=True)
    
    # Провайдер
    provider_name = Column(String, nullable=True)
    provider_type = Column(String, nullable=True)  # DOCTOR, MEDIC, NURSE
    facility = Column(String, nullable=True)
    
    # Дати
    encounter_date = Column(DateTime, nullable=True)
    discharge_date = Column(DateTime, nullable=True)
    
    # Результати
    outcome = Column(String, nullable=True)  # RECOVERED, ONGOING, TRANSFERRED, DECEASED
    return_to_duty_date = Column(DateTime, nullable=True)
    limited_duty = Column(Boolean, default=False)
    limited_duty_end_date = Column(DateTime, nullable=True)
    
    # Класифікація травми
    injury_type = Column(String, nullable=True)  # COMBAT, ACCIDENT, ILLNESS
    injury_mechanism = Column(String, nullable=True)
    injury_severity = Column(String, nullable=True)  # MINOR, MODERATE, SEVERE, CRITICAL
    
    # Пов'язані документи
    documents = Column(JSON, nullable=True)
    
    # Метадані
    recorded_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class DeploymentRecord(Base):
    """Запис про розгортання/деплоймент."""
    __tablename__ = "deployment_records"
    
    id = Column(String, primary_key=True)
    service_member_id = Column(String, ForeignKey("service_members.id"), nullable=False)
    
    # Інформація про розгортання
    operation_name = Column(String, nullable=True)
    location = Column(String, nullable=True)
    theater = Column(String, nullable=True)  # Театр бойових дій
    unit_command = Column(String, nullable=True)
    
    # Дати
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    duration_days = Column(Integer, nullable=True)
    
    # Тип місії
    mission_type = Column(String, nullable=True)  # COMBAT, TRAINING, PEACEKEEPING
    role = Column(String, nullable=True)  # Роль під час розгортання
    
    # Статус
    status = Column(String, default="PLANNED")  # PLANNED, ACTIVE, COMPLETED, CANCELLED
    
    # Пов'язані події
    events = Column(JSON, nullable=True)  # Події під час розгортання
    injuries = Column(JSON, nullable=True)  # Травми під час розгортання
    awards = Column(JSON, nullable=True)  # Нагороди
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class PersonnelDocument(Base):
    """Документи особової справи."""
    __tablename__ = "personnel_documents"
    
    id = Column(String, primary_key=True)
    service_member_id = Column(String, ForeignKey("service_members.id"), nullable=False)
    
    # Інформація про документ
    document_type = Column(String, nullable=False)  # CONTRACT, ORDERS, CERTIFICATE
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    # Файл
    filename = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    checksum = Column(String, nullable=True)
    
    # Дати
    document_date = Column(DateTime, nullable=True)  # Дата документа
    effective_date = Column(DateTime, nullable=True)  # Дата набрання чинності
    expiry_date = Column(DateTime, nullable=True)  # Термін дії
    
    # Хто видав
    issuing_authority = Column(String, nullable=True)
    authorizing_official = Column(String, nullable=True)
    
    # Статус
    status = Column(String, default="ACTIVE")  # ACTIVE, EXPIRED, REVOKED, SUPERSEDED
    is_classified = Column(Boolean, default=False)
    classification_level = Column(String, nullable=True)
    
    # Метадані
    uploaded_by = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
