"""Enhanced security dependencies for API."""
from typing import Annotated, Dict, Any, Optional
from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.api.deps import get_current_user, get_session
from app.core.security import (
    SecurityContext, 
    Permission, 
    UserRole,
    validate_data_access,
    filter_sensitive_data
)

logger = structlog.get_logger()


def get_security_context(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SecurityContext:
    """Get security context for current user."""
    return SecurityContext(current_user)


def require_permission(permission: Permission):
    """Dependency to require specific permission."""
    def permission_dependency(
        security_ctx: SecurityContext = Depends(get_security_context)
    ):
        if not security_ctx.has_permission(permission):
            logger.warning("Permission denied",
                         user_id=security_ctx.user_id,
                         user_role=security_ctx.role,
                         required_permission=permission.value)
            raise HTTPException(
                status_code=403,
                detail=f"Недостатньо прав для виконання дії: {permission.value}"
            )
        return security_ctx
    return permission_dependency


def require_personnel_access(
    security_ctx: SecurityContext = Depends(get_security_context)
) -> SecurityContext:
    """Require personnel management access."""
    required_permissions = [
        Permission.READ_PERSONNEL,
        Permission.CREATE_PERSONNEL,
        Permission.UPDATE_PERSONNEL
    ]
    
    for perm in required_permissions:
        if security_ctx.has_permission(perm):
            return security_ctx
    
    logger.warning("Personnel access denied",
                 user_id=security_ctx.user_id,
                 user_role=security_ctx.role)
    raise HTTPException(
        status_code=403,
        detail="Недостатньо прав для управління персоналом"
    )


def require_medical_access(
    security_ctx: SecurityContext = Depends(get_security_context)
) -> SecurityContext:
    """Require medical records access."""
    required_permissions = [
        Permission.READ_MEDICAL,
        Permission.CREATE_MEDICAL,
        Permission.UPDATE_MEDICAL
    ]
    
    for perm in required_permissions:
        if security_ctx.has_permission(perm):
            return security_ctx
    
    logger.warning("Medical access denied",
                 user_id=security_ctx.user_id,
                 user_role=security_ctx.role)
    raise HTTPException(
        status_code=403,
        detail="Недостатньо прав для доступу до медичних записів"
    )


def validate_unit_access(
    target_unit: Optional[str] = None,
    security_ctx: SecurityContext = Depends(get_security_context)
) -> SecurityContext:
    """Validate unit access for operations."""
    if target_unit and not security_ctx.can_access_unit(target_unit):
        logger.warning("Unit access denied",
                     user_id=security_ctx.user_id,
                     user_unit=security_ctx.unit,
                     target_unit=target_unit)
        raise HTTPException(
            status_code=403,
            detail=f"Доступ заборонено до підрозділу: {target_unit}"
        )
    return security_ctx


async def get_member_with_access_check(
    member_id: str,
    session: AsyncSession = Depends(get_session),
    security_ctx: SecurityContext = Depends(get_security_context)
):
    """Get service member with access validation."""
    from app.models.personnel import ServiceMember
    
    try:
        member = await session.get(ServiceMember, member_id)
        if not member:
            raise HTTPException(
                status_code=404,
                detail="Військовослужбовця не знайдено"
            )
        
        # Convert to dict for validation
        member_data = {
            "id": member.id,
            "unit": member.unit,
            "service_number": member.service_number,
            "last_name": member.last_name,
            "first_name": member.first_name,
        }
        
        # Validate access
        if not validate_data_access(security_ctx.user, member_data, "read"):
            raise HTTPException(
                status_code=403,
                detail="Доступ заборонено"
            )
        
        return member
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get member with access check",
                    member_id=member_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Помилка при отриманні даних"
        )


def filter_response_data(
    data: Dict[str, Any],
    security_ctx: SecurityContext = Depends(get_security_context)
) -> Dict[str, Any]:
    """Filter response data based on user permissions."""
    return security_ctx.filter_data(data)


def audit_operation(
    operation: str,
    resource_type: str,
    resource_id: str,
    security_ctx: SecurityContext = Depends(get_security_context),
    success: bool = True,
    details: Optional[Dict[str, Any]] = None
):
    """Audit operation for compliance."""
    logger.info("Operation audited",
               operation=operation,
               resource_type=resource_type,
               resource_id=resource_id,
               user_id=security_ctx.user_id,
               user_role=security_ctx.role,
               user_unit=security_ctx.unit,
               success=success,
               details=details or {})


# Specific permission dependencies
def RequireAdmin():
    return Depends(require_permission(Permission.SYSTEM_CONFIG))

def RequirePersonnelCreate():
    return Depends(require_permission(Permission.CREATE_PERSONNEL))

def RequirePersonnelRead():
    return Depends(require_permission(Permission.READ_PERSONNEL))

def RequirePersonnelUpdate():
    return Depends(require_permission(Permission.UPDATE_PERSONNEL))

def RequirePersonnelDelete():
    return Depends(require_permission(Permission.DELETE_PERSONNEL))

def RequireMedicalRead():
    return Depends(require_permission(Permission.READ_MEDICAL))

def RequireMedicalCreate():
    return Depends(require_permission(Permission.CREATE_MEDICAL))

def RequireExportData():
    return Depends(require_permission(Permission.EXPORT_DATA))
