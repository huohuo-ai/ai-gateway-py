"""Admin routes."""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ModelStatus, UserRole, UserStatus
from app.core.exceptions import (
    ModelNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.db import get_db
from app.middleware.auth import require_admin
from app.schemas import (
    AIModelCreate,
    AIModelResponse,
    AIModelUpdate,
    AuditLogQuery,
    RiskEventResolveRequest,
    UserCreate,
    UserQuotaResponse,
    UserQuotaUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.ai_model_service import AIModelService
from app.services.audit_service import AuditService
from app.services.quota_service import QuotaService
from app.services.user_service import UserService

router = APIRouter()


# ==================== Model Management ====================

@router.get("/models", response_model=dict)
async def list_models_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ModelStatus] = None,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """List all models (admin only)."""
    service = AIModelService(db)
    models, total = await service.list_models(page, page_size, status)
    
    return {
        "data": [AIModelResponse.model_validate(m) for m in models],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/models", response_model=AIModelResponse)
async def create_model(
    data: AIModelCreate,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Create new AI model (admin only)."""
    service = AIModelService(db)
    model = await service.create(data)
    
    return AIModelResponse.model_validate(model)


@router.get("/models/{model_id}", response_model=AIModelResponse)
async def get_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get model by ID (admin only)."""
    service = AIModelService(db)
    model = await service.get_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    return AIModelResponse.model_validate(model)


@router.put("/models/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: int,
    data: AIModelUpdate,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Update model (admin only)."""
    service = AIModelService(db)
    
    try:
        model = await service.update(model_id, data)
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    return AIModelResponse.model_validate(model)


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Delete model (admin only)."""
    service = AIModelService(db)
    
    try:
        await service.delete(model_id)
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    return {"message": "Model deleted successfully"}


@router.patch("/models/{model_id}/status")
async def toggle_model_status(
    model_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Toggle model status (admin only)."""
    service = AIModelService(db)
    model = await service.get_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    is_active = data.get("is_active", True)
    new_status = ModelStatus.ACTIVE if is_active else ModelStatus.INACTIVE
    await service.update(model_id, AIModelUpdate(status=new_status))
    
    return {"message": "Model status updated"}


# ==================== User Management ====================

@router.get("/users", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """List all users (admin only)."""
    service = UserService(db)
    users, total = await service.list_users(page, page_size, role, status)
    
    return {
        "data": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/users", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Create new user (admin only)."""
    service = UserService(db)
    
    try:
        user = await service.create(data)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return UserResponse.model_validate(user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get user by ID (admin only)."""
    service = UserService(db)
    user = await service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Update user (admin only)."""
    service = UserService(db)
    
    try:
        user = await service.update(user_id, data)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Delete user (admin only)."""
    service = UserService(db)
    
    try:
        await service.delete(user_id)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Reset user password (admin only)."""
    service = UserService(db)
    new_password = data.get("new_password", "password123")
    
    try:
        await service.reset_password(user_id, new_password)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password reset successfully"}


@router.get("/users/{user_id}/quota", response_model=UserQuotaResponse)
async def get_user_quota(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get user quota (admin only)."""
    service = QuotaService(db)
    quota = await service.get_quota(user_id)
    
    return UserQuotaResponse.model_validate(quota)


@router.put("/users/{user_id}/quota", response_model=UserQuotaResponse)
async def update_user_quota(
    user_id: int,
    data: UserQuotaUpdate,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Update user quota (admin only)."""
    service = QuotaService(db)
    quota = await service.update_quota(
        user_id,
        daily_limit=data.daily_limit,
        weekly_limit=data.weekly_limit,
        monthly_limit=data.monthly_limit
    )
    
    return UserQuotaResponse.model_validate(quota)


# ==================== Audit Management ====================

@router.get("/audit-logs")
async def query_audit_logs(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    user_id: Optional[int] = None,
    model_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Query audit logs (admin only)."""
    from datetime import datetime
    
    service = AuditService(db)
    
    start = None
    end = None
    if start_time:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    if end_time:
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    result = await service.query_logs(
        start_time=start,
        end_time=end,
        user_id=user_id,
        model_name=model_name,
        page=page,
        page_size=page_size
    )
    
    return result


@router.get("/audit-logs/export")
async def export_audit_logs(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    user_id: Optional[int] = None,
    model_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Export audit logs as CSV (admin only)."""
    import csv
    import io
    from datetime import datetime

    from fastapi.responses import StreamingResponse

    service = AuditService(db)

    start = None
    end = None
    if start_time:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    if end_time:
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

    logs, _ = await service.query_logs(
        start_time=start,
        end_time=end,
        user_id=user_id,
        model_name=model_name,
        page=1,
        page_size=10000
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "timestamp", "request_id", "user_id", "user_name", "model_name",
        "prompt_tokens", "completion_tokens", "total_tokens", "latency_ms",
        "response_status", "request_ip"
    ])
    for log in logs:
        writer.writerow([
            log.get("timestamp", ""),
            log.get("request_id", ""),
            log.get("user_id", ""),
            log.get("user_name", ""),
            log.get("model_name", ""),
            log.get("prompt_tokens", 0),
            log.get("completion_tokens", 0),
            log.get("total_tokens", 0),
            log.get("latency_ms", 0),
            log.get("response_status", ""),
            log.get("request_ip", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )


@router.get("/risk-alerts")
async def get_risk_events(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    risk_level: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get risk events (admin only)."""
    from datetime import datetime
    
    service = AuditService(db)
    
    start = None
    end = None
    if start_time:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    if end_time:
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    events, total = await service.get_risk_events(
        start_time=start,
        end_time=end,
        risk_level=risk_level,
        page=page,
        page_size=page_size
    )
    
    return {
        "data": events,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/risk-alerts/{event_id}")
async def resolve_risk_event(
    event_id: str,
    data: RiskEventResolveRequest,
    current_admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Resolve a risk event (admin only)."""
    service = AuditService(db)
    
    await service.resolve_risk_event(
        event_id=event_id,
        resolved_by=current_admin.username,
        note=data.note or ""
    )
    
    return {"message": "Risk event resolved successfully"}


@router.get("/users/{user_id}/statistics")
async def get_user_statistics(
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get user statistics (admin only)."""
    from datetime import datetime, timedelta
    
    service = AuditService(db)
    
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start = datetime.now() - timedelta(days=30)
        start_date = start.strftime("%Y-%m-%d")
    
    stats = await service.get_user_statistics(user_id, start_date, end_date)
    
    return {"data": stats}


# ==================== Dashboard & Statistics ====================

@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get dashboard statistics (admin only)."""
    service = AuditService(db)
    stats = await service.get_dashboard_stats()
    
    return stats


@router.get("/usage-trend")
async def get_usage_trend(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get usage trend (admin only)."""
    return []


@router.get("/recent-requests")
async def get_recent_requests(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get recent requests (admin only)."""
    return []


@router.get("/risk-stats")
async def get_risk_stats(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get risk statistics (admin only)."""
    return {"total": 0, "resolved": 0, "pending": 0}


@router.get("/audit-stats")
async def get_audit_stats(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get audit statistics (admin only)."""
    return {"total_logs": 0, "total_tokens": 0}


# ==================== Risk Rules ====================

@router.get("/risk-rules")
async def list_risk_rules(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """List risk rules (admin only)."""
    return []


@router.put("/risk-rules/{rule_id}")
async def update_risk_rule(
    rule_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Update risk rule (admin only)."""
    return {"message": "Rule updated"}
