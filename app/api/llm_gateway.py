"""LLM Gateway routes (OpenAI compatible, API Key auth)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ModelError, ModelNotFoundError, QuotaExceededError
from app.db import get_db
from app.middleware.auth import verify_api_key
from app.schemas import ChatCompletionRequest
from app.services.llm_service import LLMService

router = APIRouter(prefix="/v1")


@router.get("/models")
async def list_models_gateway(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_api_key)
):
    """List available models (API Key auth)."""
    service = LLMService(db)
    models = await service.list_models()
    
    # Format as OpenAI compatible
    data = []
    for i, m in enumerate(models):
        from datetime import datetime
        data.append({
            "id": m.get("model_id", str(m.get("id"))),
            "object": "model",
            "created": int(datetime.utcnow().timestamp()),
            "owned_by": m.get("provider", "custom"),
        })
    
    return {"object": "list", "data": data}


@router.post("/chat/completions")
async def chat_completions_gateway(
    request: Request,
    data: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_api_key)
):
    """Chat completions endpoint (API Key auth, OpenAI compatible)."""
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
                    "type": "insufficient_quota",
                    "param": None,
                    "code": "insufficient_quota",
                }
            }
        )
    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "message": str(e),
                    "type": "invalid_request_error",
                    "param": "model",
                    "code": "model_not_found",
                }
            }
        )
    except ModelError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": {
                    "message": str(e),
                    "type": "api_error",
                    "param": None,
                    "code": "llm_error",
                }
            }
        )
