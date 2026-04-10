"""Admin routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ModelStatus
from app.core.exceptions import ModelNotFoundError
from app.db import get_db
from app.middleware.auth import require_admin
from app.schemas import (
    AIModelCreate,
    AIModelResponse,
    AIModelUpdate,
    AuditLogQuery,
    RiskEventResolveRequest,
)
from app.services.ai_model_service import AIModelService
from app.services.audit_service import AuditService

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


# ==================== Audit Management ====================

@router.get("/audit/logs")
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
    
    # Parse times
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


@router.get("/audit/risk-events")
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
    
    # Parse times
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


@router.post("/audit/risk-events/{event_id}/resolve")
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


@router.get("/audit/users/{user_id}/statistics")
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
    
    # Default date range: last 30 days
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start = datetime.now() - timedelta(days=30)
        start_date = start.strftime("%Y-%m-%d")
    
    stats = await service.get_user_statistics(user_id, start_date, end_date)
    
    return {"data": stats}


@router.get("/audit/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    """Get dashboard statistics (admin only)."""
    service = AuditService(db)
    stats = await service.get_dashboard_stats()
    
    return stats
