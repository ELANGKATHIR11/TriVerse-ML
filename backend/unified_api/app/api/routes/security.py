from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.audit import AuditLog

router = APIRouter(prefix="/security", tags=["security"])

@router.get("/audit-logs", response_model=List[Dict[str, Any]])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Retrieve security audit trails (Admin only)."""
    stmt = select(AuditLog).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
    logs = (await db.execute(stmt)).scalars().all()
    
    return [{
        "id": l.id,
        "user_id": l.user_id,
        "action": l.action,
        "resource": l.resource,
        "resource_id": l.resource_id,
        "details": l.details_json,
        "ip_address": l.ip_address,
        "user_agent": l.user_agent,
        "created_at": l.created_at.isoformat()
    } for l in logs]

@router.get("/stats", response_model=Dict[str, Any])
async def get_security_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Retrieve basic security stats summary."""
    total_logs_stmt = select(func.count(AuditLog.id))
    total_logs = (await db.execute(total_logs_stmt)).scalar() or 0
    
    # Simple active users counting
    active_stmt = select(func.count(User.id)).where(User.is_active == True)
    active_count = (await db.execute(active_stmt)).scalar() or 0
    
    return {
        "total_audit_events": total_logs,
        "active_users": active_count,
        "mfa_status": "disabled",
        "encryption_algorithm": "AES-256-GCM"
    }
