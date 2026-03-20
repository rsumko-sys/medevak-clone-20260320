"""Pydantic schemas for personnel validation."""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, EmailStr
import re


class ServiceMemberCreate(BaseModel):
    """Schema for creating service member."""
    
    # Ідентифікація
    service_number: str = Field(..., min_length=3, max_length=20, description="Військовий номер")
    social_security: Optional[str] = Field(None, min_length=9, max_length=11, description="Соціальний номер")
    
    # Персональні дані
    last_name: str = Field(..., min_length=2, max_length=50, description="Прізвище")
    first_name: str = Field(..., min_length=2, max_length=50, description="Ім'я")
    middle_name: Optional[str] = Field(None, max_length=50, description="По батькові")
    date_of_birth: Optional[date] = Field(None, description="Дата народження")
    place_of_birth: Optional[str] = Field(None, max_length=100, description="Місце народження")
    citizenship: Optional[str] = Field("Україна", max_length=50, description="Громадянство")
    
    # Військові дані
    rank: Optional[str] = Field(None, max_length=50, description="Звання")
    specialty: Optional[str] = Field(None, max_length=100, description="Спеціальність/MOS")
    unit: Optional[str] = Field(None, max_length=100, description="Підрозділ")
    position: Optional[str] = Field(None, max_length=100, description="Посада")
    
    # Служба
    enlistment_date: Optional[date] = Field(None, description="Дата призову/контракту")
    service_start_date: Optional[date] = Field(None, description="Початок служби")
    contract_end_date: Optional[date] = Field(None, description="Кінець контракту")
    years_of_service: Optional[float] = Field(None, ge=0, le=50, description="Вислуга років")
    
    # Контактна інформація
    phone: Optional[str] = Field(None, max_length=20, description="Телефон")
    email: Optional[EmailStr] = Field(None, description="Email")
    address: Optional[str] = Field(None, max_length=500, description="Адреса")
    emergency_contact: Optional[Dict[str, Any]] = Field(None, description="Контактна особа")
    
    # Медичні дані
    blood_type: Optional[str] = Field(None, description="Група крові")
    allergies: Optional[str] = Field(None, max_length=1000, description="Алергії")
    medical_conditions: Optional[str] = Field(None, max_length=1000, description="Хронічні захворювання")
    medications: Optional[str] = Field(None, max_length=1000, description="Постійні ліки")
    last_physical_date: Optional[date] = Field(None, description="Останній медогляд")
    
    # Бойовий досвід
    deployments: Optional[List[Dict[str, Any]]] = Field(None, description="Список розгортань")
    combat_experience: bool = Field(False, description="Бойовий досвід")
    awards: Optional[List[Dict[str, Any]]] = Field(None, description="Нагороди")
    qualifications: Optional[List[Dict[str, Any]]] = Field(None, description="Кваліфікації")
    
    # Статус
    status: str = Field("ACTIVE", description="Статус")
    is_deployed: bool = Field(False, description="На розгортанні")

    @field_validator('service_number')
    @classmethod
    def validate_service_number(cls, v):
        """Валідація військового номера."""
        if not re.match(r'^[A-Z0-9]{3,20}$', v):
            raise ValueError('Військовий номер повинен містити лише великі літери та цифри')
        return v.upper()
    
    @field_validator('social_security')
    @classmethod
    def validate_social_security(cls, v):
        """Валідація соціального номера."""
        if v and not re.match(r'^\d{9,11}$', v):
            raise ValueError('Соціальний номер повинен містити 9-11 цифр')
        return v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_age(cls, v):
        """Перевірка віку."""
        if v:
            today = date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            if age < 18:
                raise ValueError('Військовослужбовець повинен бути повнолітнім')
            if age > 65:
                raise ValueError('Перевірте вік - занадто великий')
        return v
    
    @field_validator('blood_type')
    @classmethod
    def validate_blood_type(cls, v):
        """Валідація групи крові."""
        if v:
            valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            if v not in valid_types:
                raise ValueError(f'Група крові повинна бути однією з: {", ".join(valid_types)}')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Валідація телефону."""
        if v:
            # Приймаємо формати: +380501234567, 0501234567, 380501234567
            v = re.sub(r'[^\d+]', '', v)
            if not re.match(r'^\+?\d{10,15}$', v):
                raise ValueError('Невірний формат телефону')
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Валідація статусу."""
        valid_statuses = ['ACTIVE', 'INACTIVE', 'DEPLOYED', 'MEDICAL_HOLD', 'RETIRED']
        if v not in valid_statuses:
            raise ValueError(f'Статус повинен бути однією з: {", ".join(valid_statuses)}')
        return v
    
    @field_validator('contract_end_date')
    @classmethod
    def validate_contract_dates(cls, v, info):
        """Перевірка дат контракту."""
        if v and 'enlistment_date' in info.data and info.data['enlistment_date']:
            if v <= info.data['enlistment_date']:
                raise ValueError('Кінець контракту повинен бути після початку')
        return v


class ServiceMemberUpdate(BaseModel):
    """Schema for updating service member."""
    
    # Оновлювані поля (опціональні)
    service_number: Optional[str] = Field(None, min_length=3, max_length=20)
    social_security: Optional[str] = Field(None, min_length=9, max_length=11)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    place_of_birth: Optional[str] = Field(None, max_length=100)
    citizenship: Optional[str] = Field(None, max_length=50)
    rank: Optional[str] = Field(None, max_length=50)
    specialty: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    enlistment_date: Optional[date] = None
    service_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    years_of_service: Optional[float] = Field(None, ge=0, le=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, max_length=500)
    emergency_contact: Optional[Dict[str, Any]] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = Field(None, max_length=1000)
    medical_conditions: Optional[str] = Field(None, max_length=1000)
    medications: Optional[str] = Field(None, max_length=1000)
    last_physical_date: Optional[date] = None
    deployments: Optional[List[Dict[str, Any]]] = None
    combat_experience: Optional[bool] = None
    awards: Optional[List[Dict[str, Any]]] = None
    qualifications: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    is_deployed: Optional[bool] = None

    # Використовуємо ті ж самі валідатори
    _validate_service_number = field_validator('service_number')(ServiceMemberCreate.validate_service_number)
    _validate_social_security = field_validator('social_security')(ServiceMemberCreate.validate_social_security)
    _validate_blood_type = field_validator('blood_type')(ServiceMemberCreate.validate_blood_type)
    _validate_phone = field_validator('phone')(ServiceMemberCreate.validate_phone)
    _validate_status = field_validator('status')(ServiceMemberCreate.validate_status)


class MedicalRecordCreate(BaseModel):
    """Schema for creating medical record."""
    
    record_type: str = Field(..., description="Тип запису")
    case_id: Optional[str] = Field(None, description="ID кейсу")
    diagnosis: Optional[str] = Field(None, max_length=500, description="Діагноз")
    diagnosis_code: Optional[str] = Field(None, max_length=20, description="Код діагнозу (ICD-10)")
    treatment: Optional[str] = Field(None, max_length=2000, description="Лікування")
    medications: Optional[str] = Field(None, max_length=1000, description="Ліки")
    procedures: Optional[str] = Field(None, max_length=1000, description="Процедури")
    provider_name: Optional[str] = Field(None, max_length=100, description="Провайдер")
    provider_type: Optional[str] = Field(None, description="Тип провайдера")
    facility: Optional[str] = Field(None, max_length=200, description="Заклад")
    encounter_date: Optional[datetime] = Field(None, description="Дата візиту")
    discharge_date: Optional[datetime] = Field(None, description="Дата виписки")
    outcome: Optional[str] = Field(None, description="Результат")
    return_to_duty_date: Optional[datetime] = Field(None, description="Повернення до служби")
    limited_duty: bool = Field(False, description="Обмежена служба")
    limited_duty_end_date: Optional[datetime] = Field(None, description="Кінець обмеженої служби")
    injury_type: Optional[str] = Field(None, description="Тип травми")
    injury_mechanism: Optional[str] = Field(None, max_length=500, description="Механізм травми")
    injury_severity: Optional[str] = Field(None, description="Важкість травми")

    @field_validator('record_type')
    @classmethod
    def validate_record_type(cls, v):
        """Валідація типу запису."""
        valid_types = ['EXAMINATION', 'INJURY', 'TREATMENT', 'VACCINATION', 'PROCEDURE', 'CONSULTATION']
        if v not in valid_types:
            raise ValueError(f'Тип запису повинен бути однією з: {", ".join(valid_types)}')
        return v
    
    @field_validator('provider_type')
    @classmethod
    def validate_provider_type(cls, v):
        """Валідація типу провайдера."""
        if v:
            valid_types = ['DOCTOR', 'MEDIC', 'NURSE', 'PARAMEDIC', 'SURGEON', 'SPECIALIST']
            if v not in valid_types:
                raise ValueError(f'Тип провайдера повинен бути однією з: {", ".join(valid_types)}')
        return v
    
    @field_validator('injury_severity')
    @classmethod
    def validate_injury_severity(cls, v):
        """Валідація важкості травми."""
        if v:
            valid_severities = ['MINOR', 'MODERATE', 'SEVERE', 'CRITICAL']
            if v not in valid_severities:
                raise ValueError(f'Важкість травми повинна бути однією з: {", ".join(valid_severities)}')
        return v
    
    @field_validator('discharge_date')
    @classmethod
    def validate_dates(cls, v, info):
        """Перевірка дат."""
        if v and 'encounter_date' in info.data and info.data['encounter_date']:
            if v <= info.data['encounter_date']:
                raise ValueError('Дата виписки повинна бути після дати візиту')
        return v


class ServiceMemberResponse(BaseModel):
    """Schema for service member response."""
    
    id: str
    service_number: Optional[str]
    social_security: Optional[str]
    last_name: Optional[str]
    first_name: Optional[str]
    middle_name: Optional[str]
    date_of_birth: Optional[datetime]
    place_of_birth: Optional[str]
    citizenship: Optional[str]
    rank: Optional[str]
    specialty: Optional[str]
    unit: Optional[str]
    position: Optional[str]
    enlistment_date: Optional[datetime]
    service_start_date: Optional[datetime]
    contract_end_date: Optional[datetime]
    years_of_service: Optional[float]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    emergency_contact: Optional[Dict[str, Any]]
    blood_type: Optional[str]
    allergies: Optional[str]
    medical_conditions: Optional[str]
    medications: Optional[str]
    last_physical_date: Optional[datetime]
    deployments: Optional[List[Dict[str, Any]]]
    combat_experience: bool
    awards: Optional[List[Dict[str, Any]]]
    qualifications: Optional[List[Dict[str, Any]]]
    status: str
    is_deployed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PersonnelListResponse(BaseModel):
    """Schema for personnel list response."""
    
    data: List[ServiceMemberResponse]
    total: int
    offset: int
    limit: int


class ErrorResponse(BaseModel):
    """Schema for error response."""
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
