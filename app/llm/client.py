"""LLM client for making requests to various providers."""
import json
from typing import AsyncGenerator, Optional

import httpx

from app.config import settings
from app.models import AIModel


class LLMClient:
    """HTTP client for LLM API requests."""
    
    def __init__(self, model: AIModel):
        self.model = model
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=model.timeout or settings.llm.default_timeout,
            write=10.0,
            pool=10.0
        )
    
    def _get_headers(self) -> dict:
        """Get request headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.model.api_key}",
        }
    
    def _build_url(self, endpoint: str = "chat/completions") -> str:
        """Build API URL."""
        base_url = self.model.base_url.rstrip("/")
        return f"{base_url}/{endpoint}"
    
    def _prepare_request_body(self, request_data: dict) -> dict:
        """Prepare request body with model-specific settings."""
        body = {
            "model": self.model.model_id,
            "messages": request_data.get("messages", []),
        }
        
        # Add optional parameters
        if "temperature" in request_data:
            body["temperature"] = request_data["temperature"]
        elif self.model.temperature:
            body["temperature"] = self.model.temperature
        
        if "max_tokens" in request_data:
            body["max_tokens"] = request_data["max_tokens"]
        elif self.model.max_tokens:
            body["max_tokens"] = self.model.max_tokens
        
        if "top_p" in request_data:
            body["top_p"] = request_data["top_p"]
        
        if "stream" in request_data:
            body["stream"] = request_data["stream"]
        
        if "stop" in request_data:
            body["stop"] = request_data["stop"]
        
        # Add system prompt if configured and not already present
        if self.model.system_prompt:
            messages = body.get("messages", [])
            has_system = any(
                msg.get("role") == "system" for msg in messages
            )
            if not has_system:
                body["messages"] = [
                    {"role": "system", "content": self.model.system_prompt}
                ] + messages
        
        return body
    
    async def chat_completion(self, request_data: dict) -> dict:
        """Make a non-streaming chat completion request."""
        body = self._prepare_request_body(request_data)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self._build_url(),
                headers=self._get_headers(),
                json=body
            )
            response.raise_for_status()
            return response.json()
    
    async def chat_completion_stream(
        self,
        request_data: dict
    ) -> AsyncGenerator[str, None]:
        """Make a streaming chat completion request."""
        body = self._prepare_request_body(request_data)
        body["stream"] = True
        
        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"
        headers["Cache-Control"] = "no-cache"
        headers["Connection"] = "keep-alive"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                self._build_url(),
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        yield line + "\n"


async def get_client_by_model(
    model_name: str,
    db_session
) -> Optional[LLMClient]:
    """Get LLM client by model name or ID."""
    from app.services.ai_model_service import AIModelService
    
    service = AIModelService(db_session)
    
    # Try to get by name first
    model = await service.get_by_name(model_name)
    if not model:
        # Try by model_id
        model = await service.get_by_model_id(model_name)
    if not model:
        # Try by ID
        try:
            model_id = int(model_name)
            model = await service.get_by_id(model_id)
        except ValueError:
            pass
    
    if not model or not model.is_active:
        return None
    
    return LLMClient(model)


async def get_default_client(db_session) -> Optional[LLMClient]:
    """Get default LLM client."""
    from app.services.ai_model_service import AIModelService
    
    service = AIModelService(db_session)
    model = await service.get_default_model()
    
    if not model:
        return None
    
    return LLMClient(model)
