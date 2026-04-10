"""LLM service for handling chat completions."""
import json
import time
from datetime import datetime

from fastapi import Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import REQUEST_ID_HEADER
from app.core.exceptions import ModelError, ModelNotFoundError, QuotaExceededError
from app.core.security import generate_uuid
from app.llm.client import get_client_by_model, get_default_client
from app.models import UsageLog
from app.schemas import ChatCompletionRequest
from app.services.ai_model_service import AIModelService
from app.services.quota_service import QuotaService


class LLMService:
    """LLM business service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_service = AIModelService(db)
        self.quota_service = QuotaService(db)
    
    async def chat_completion(
        self,
        request: Request,
        user_id: int,
        data: ChatCompletionRequest,
        username: str = ""
    ):
        """Handle chat completion request."""
        request_id = generate_uuid()
        start_time = time.time()
        
        # Get model
        if data.model:
            client = await get_client_by_model(data.model, self.db)
            model_name = data.model
        else:
            client = await get_default_client(self.db)
            if client:
                model_name = client.model.name
        
        if not client:
            raise ModelNotFoundError(f"Model '{data.model}' not found or not active")
        
        # Check quota before request
        messages = [msg.model_dump() for msg in data.messages]
        await self.quota_service.check_before_request(
            user_id,
            messages,
            data.max_tokens or 0
        )
        
        # Prepare request data
        request_data = {
            "messages": messages,
            "temperature": data.temperature,
            "max_tokens": data.max_tokens,
            "top_p": data.top_p,
            "stream": data.stream,
            "stop": data.stop,
        }
        
        if data.stream:
            return await self._handle_streaming(
                client,
                request_data,
                user_id,
                username,
                model_name,
                request_id,
                start_time
            )
        else:
            return await self._handle_non_streaming(
                client,
                request_data,
                user_id,
                username,
                model_name,
                request_id,
                start_time
            )
    
    async def _handle_non_streaming(
        self,
        client,
        request_data: dict,
        user_id: int,
        username: str,
        model_name: str,
        request_id: str,
        start_time: float
    ):
        """Handle non-streaming request."""
        try:
            response = await client.chat_completion(request_data)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract usage
            usage = response.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            # Consume quota
            await self.quota_service.consume_after_request(user_id, total_tokens)
            
            # Record usage
            await self._record_usage(
                user_id=user_id,
                request_id=request_id,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                status="success"
            )
            
            # Add request ID to response
            response["id"] = request_id
            
            return response
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            await self._record_usage(
                user_id=user_id,
                request_id=request_id,
                model_name=model_name,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=latency_ms,
                status="failed",
                error_message=str(e)
            )
            raise ModelError(f"LLM request failed: {str(e)}")
    
    async def _handle_streaming(
        self,
        client,
        request_data: dict,
        user_id: int,
        username: str,
        model_name: str,
        request_id: str,
        start_time: float
    ):
        """Handle streaming request."""
        total_tokens = 0
        full_content = ""
        
        async def generate():
            nonlocal total_tokens, full_content
            
            try:
                async for line in client.chat_completion_stream(request_data):
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        
                        if data_str == "[DONE]":
                            # Calculate tokens from content
                            completion_tokens = len(full_content) // 4
                            prompt_tokens = sum(
                                len(msg.get("content", "")) // 4
                                for msg in request_data.get("messages", [])
                            )
                            total_tokens = prompt_tokens + completion_tokens
                            
                            latency_ms = int((time.time() - start_time) * 1000)
                            
                            # Consume quota
                            await self.quota_service.consume_after_request(
                                user_id, total_tokens
                            )
                            
                            # Record usage
                            await self._record_usage(
                                user_id=user_id,
                                request_id=request_id,
                                model_name=model_name,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                total_tokens=total_tokens,
                                latency_ms=latency_ms,
                                status="success"
                            )
                            
                            yield "data: [DONE]\n\n"
                            break
                        
                        try:
                            data = json.loads(data_str)
                            # Accumulate content for token estimation
                            choices = data.get("choices", [])
                            for choice in choices:
                                delta = choice.get("delta", {})
                                content = delta.get("content", "")
                                full_content += content
                            
                            yield line
                        except json.JSONDecodeError:
                            yield line
                            
            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                await self._record_usage(
                    user_id=user_id,
                    request_id=request_id,
                    model_name=model_name,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    latency_ms=latency_ms,
                    status="failed",
                    error_message=str(e)
                )
                raise
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                REQUEST_ID_HEADER: request_id,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    async def _record_usage(
        self,
        user_id: int,
        request_id: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: int,
        status: str,
        error_message: str = ""
    ):
        """Record usage log."""
        now = datetime.utcnow()
        request_time = datetime.utcnow()
        
        log = UsageLog(
            user_id=user_id,
            request_id=request_id,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            request_time=request_time,
            response_time=now,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
            ip="",
            user_agent=""
        )
        
        self.db.add(log)
        await self.db.commit()
    
    async def list_models(self) -> list[dict]:
        """List available models."""
        models = await self.model_service.get_active_models()
        return [m.to_public_dict() for m in models]
