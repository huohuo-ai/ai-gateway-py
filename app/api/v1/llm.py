"""LLM API routes (authenticated)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ModelError, ModelNotFoundError, QuotaExceededError
from app.db import get_db
from app.middleware.auth import get_current_user
from app.schemas import ChatCompletionRequest, ModelListResponse
from app.services.llm_service import LLMService

router = APIRouter()


@router.get("/models")
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List available models."""
    service = LLMService(db)
    models = await service.list_models()
    
    # Format as OpenAI compatible
    data = []
    for i, m in enumerate(models):
        from datetime import datetime
        data.append({
            "id": m.get("model_id", str(m.get("id"))),
            "name": m.get("name", m.get("model_id", str(m.get("id")))),
            "object": "model",
            "created": int(datetime.utcnow().timestamp()),
            "owned_by": m.get("provider", "custom"),
        })
    
    return {"object": "list", "data": data}


@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    data: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Chat completions endpoint (OpenAI compatible)."""
    service = LLMService(db)
    
    try:
        return await service.chat_completion(
            request=request,
            user_id=current_user.id,
            data=data,
            username=current_user.username
        )
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "message": f"Quota exceeded: {e}",
                    "type": "quota_exceeded",
                }
            }
        )
    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "message": str(e),
                    "type": "model_not_found",
                }
            }
        )
    except ModelError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": {
                    "message": str(e),
                    "type": "llm_error",
                }
            }
        )
