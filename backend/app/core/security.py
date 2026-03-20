"""Enhanced security and role-based access control."""
from typing import Optional, List, Dict, Any
from enum import Enum
import structlog
import time
from collections import deque


logger = structlog.get_logger()


class UserRole(str, Enum):
    """User roles with hierarchy."""
    ADMIN = "admin"
    PERSONNEL = "personnel" 
    MEDIC = "medic"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Granular permissions."""
    # Personnel management
    CREATE_PERSONNEL = "create_personnel"
    READ_PERSONNEL = "read_personnel"
    UPDATE_PERSONNEL = "update_personnel"
    DELETE_PERSONNEL = "delete_personnel"
    
    # Medical records
    READ_MEDICAL = "read_medical"
    CREATE_MEDICAL = "create_medical"
    UPDATE_MEDICAL = "update_medical"
    
    # Sensitive data
    READ_SENSITIVE = "read_sensitive"
    EXPORT_DATA = "export_data"
    
    # System operations
    AUDIT_LOGS = "audit_logs"
    SYSTEM_CONFIG = "system_config"


# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.CREATE_PERSONNEL,
        Permission.READ_PERSONNEL,
        Permission.UPDATE_PERSONNEL,
        Permission.DELETE_PERSONNEL,
        Permission.READ_MEDICAL,
        Permission.CREATE_MEDICAL,
        Permission.UPDATE_MEDICAL,
        Permission.READ_SENSITIVE,
        Permission.EXPORT_DATA,
        Permission.AUDIT_LOGS,
        Permission.SYSTEM_CONFIG,
    ],
    UserRole.PERSONNEL: [
        Permission.READ_PERSONNEL,
        Permission.UPDATE_PERSONNEL,
        Permission.READ_SENSITIVE,
        Permission.EXPORT_DATA,
    ],
    UserRole.MEDIC: [
        Permission.READ_PERSONNEL,
        Permission.READ_MEDICAL,
        Permission.CREATE_MEDICAL,
        Permission.UPDATE_MEDICAL,
        Permission.READ_SENSITIVE,
        Permission.EXPORT_DATA,
    ],
    UserRole.VIEWER: [
        Permission.READ_PERSONNEL,
    ],
}


def has_permission(user_role: str, permission: Permission) -> bool:
    """Check if user role has specific permission."""
    try:
        # Resolve the role enum or default to VIEWER
        try:
            role = UserRole(user_role)
        except ValueError:
            role = UserRole.VIEWER
            
        perms = ROLE_PERMISSIONS.get(role, []) # type: ignore
        return permission in perms
    except Exception:
        return False


def can_access_unit(user_unit: str, target_unit: str, user_role: str) -> bool:
    """Check if user can access data from specific unit."""
    # Convert string to UserRole for comparison
    try:
        current_role = UserRole(user_role)
    except ValueError:
        current_role = UserRole.VIEWER

    # Admin can access all units
    if current_role == UserRole.ADMIN:
        return True
    
    # Personnel can access all units
    if current_role == UserRole.PERSONNEL:
        return True
    
    # Medic can only access same unit
    if current_role == UserRole.MEDIC:
        return user_unit == target_unit
    
    # Viewer can access basic info from all units
    if current_role == UserRole.VIEWER:
        return True
    
    return False


def can_access_sensitive_data(user_role: str, data_type: str) -> bool:
    """Check if user can access sensitive data types."""
    try:
        current_role = UserRole(user_role)
    except ValueError:
        current_role = UserRole.VIEWER

    sensitive_data_types = {
        "medical_records": [UserRole.ADMIN, UserRole.MEDIC],
        "social_security": [UserRole.ADMIN, UserRole.PERSONNEL],
        "emergency_contact": [UserRole.ADMIN, UserRole.MEDIC, UserRole.PERSONNEL],
        "address": [UserRole.ADMIN, UserRole.PERSONNEL, UserRole.MEDIC],
        "phone": [UserRole.ADMIN, UserRole.PERSONNEL, UserRole.MEDIC],
        "email": [UserRole.ADMIN, UserRole.PERSONNEL, UserRole.MEDIC],
    }
    
    allowed_roles = sensitive_data_types.get(data_type, []) # type: ignore
    return current_role in allowed_roles


def filter_sensitive_data(data: Dict[str, Any], user_role: str, user_unit: str = "") -> Dict[str, Any]:
    """Filter sensitive data based on user role and unit."""
    try:
        current_role = UserRole(user_role)
    except ValueError:
        current_role = UserRole.VIEWER

    if current_role == UserRole.ADMIN:
        return data  # Admin sees everything
    
    filtered_data = dict(data)  # Create a fresh dict
    
    # Remove sensitive fields based on role
    sensitive_fields: Dict[UserRole, List[str]] = {
        UserRole.VIEWER: [
            "social_security", "phone", "email", "address", 
            "emergency_contact", "medical_records", "personnel_records"
        ],
        UserRole.MEDIC: [
            "social_security"  # Medics don't see SSN
        ],
    }
    
    # Cast current_role to UserRole to ensure dict.get compatibility
    fields_to_remove = sensitive_fields.get(current_role, []) # type: ignore
    for field in fields_to_remove:
        if field in filtered_data:
            filtered_data[field] = None  # type: ignore
    
    # Filter nested records for medics from other units
    if user_role == UserRole.MEDIC and user_unit != data.get("unit", ""):
        for record_type in ["medical_records", "personnel_records", "deployment_records"]:
            if record_type in filtered_data:
                filtered_data[record_type] = []
    
    return filtered_data


# In-memory rate limiting store (UserID -> Deque of timestamps)
_EXPORT_THROTTLE: Dict[str, deque] = {}


class SecurityContext:

    """Enhanced Security context for military-grade access control."""
    
    def __init__(self, user: Dict[str, Any], request_id: Optional[str] = None):
        self.user = user
        self.role = UserRole(user.get("role", UserRole.VIEWER))
        self.unit = user.get("unit", "")
        self.user_id = user.get("sub", "")
        self.request_id = request_id
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has permission."""
        return has_permission(self.role, permission)
    
    def can_access_unit(self, target_unit: str) -> bool:
        """Check if user can access target unit (ABAC)."""
        return can_access_unit(self.unit, target_unit, self.role)
    
    def validate_unit_access(self, target_unit: str):
        """Strict validation of unit access. Raises exception if denied."""
        if not self.can_access_unit(target_unit):
            raise Exception(f"Access Denied: Unit isolation violation. Target: {target_unit}")

    def can_access_sensitive_data(self, data_type: str) -> bool:
        """Check if user can access sensitive data type."""
        return can_access_sensitive_data(self.role, data_type)
    
    def filter_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter data based on user permissions."""
        return filter_sensitive_data(data, self.role, self.unit)
    
    def audit_access(self, resource_id: str, action: str, success: bool = True, reason: Optional[str] = None):
        """Log access attempt for audit with request correlation."""
        logger.info("Audit log",
                   request_id=self.request_id,
                   user_id=self.user_id,
                   user_role=self.role,
                   resource_id=resource_id,
                   action=action,
                   success=success,
                   user_unit=self.unit)

    def check_rate_limit(self, action: str, limit: int = 5, window_seconds: int = 60):
        """Simple sliding window rate limiting."""
        if action != "export":
            return # Only throttling exports for now
            
        now = time.time()
        if self.user_id not in _EXPORT_THROTTLE:
            _EXPORT_THROTTLE[self.user_id] = deque()
            
        timestamps = _EXPORT_THROTTLE[self.user_id]
        
        # Remove expired timestamps
        while timestamps and timestamps[0] < now - window_seconds:
            timestamps.popleft()
            
        if len(timestamps) >= limit:
            logger.warning("Rate limit exceeded", 
                        user_id=self.user_id, 
                        action=action,
                        limit=limit)
            raise Exception(f"Rate limit exceeded: {limit} requests per {window_seconds}s")
            
        timestamps.append(now)




# require_permission deleted - moved to deps.py as FastAPI dependency



def validate_data_access(user: Dict[str, Any], target_data: Dict[str, Any], action: str = "read") -> bool:
    """Validate if user can access specific data."""
    security_ctx = SecurityContext(user)
    
    # Check basic read permission
    if action == "read" and not security_ctx.has_permission(Permission.READ_PERSONNEL):
        return False
    
    # Check unit access
    target_unit = target_data.get("unit", "")
    if not security_ctx.can_access_unit(target_unit):
        return False
    
    # Log successful access
    security_ctx.audit_access(target_data.get("id", "unknown"), action, True)
    return True


def get_accessible_units(user_role: str, user_unit: str) -> List[str]:
    """Get list of units user can access."""
    if user_role in [UserRole.ADMIN, UserRole.PERSONNEL, UserRole.VIEWER]:
        return ["*"]  # All units
    elif user_role == UserRole.MEDIC:
        return [user_unit]  # Only own unit
    return []
