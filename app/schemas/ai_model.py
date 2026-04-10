"""AI Model schemas."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ModelProvider, ModelStatus


class AIModelBase(BaseModel):
    """Base AI model schema."""
    name: str = Field(..., max_length=50)
    model_id: str = Field(..., max_length=100)
    provider: ModelProvider = ModelProvider.OPENAI
    base_url: str = Field(..., max_length=255)
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2000, gt=0)
    timeout: int = Field(60, gt=0)
    system_prompt: Optional[str] = None


class AIModelCreate(AIModelBase):
    """AI model creation schema."""
    api_key: str
    is_default: bool = False


class AIModelUpdate(BaseModel):
    """AI model update schema."""
    name: Optional[str] = Field(None, max_length=50)
    model_id: Optional[str] = Field(None, max_length=100)
    provider: Optional[ModelProvider] = None
    base_url: Optional[str] = Field(None, max_length=255)
    api_key: Optional[str] = None
    status: Optional[ModelStatus] = None
    is_default: Optional[bool] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0)
    timeout: Optional[int] = Field(None, gt=0)
    system_prompt: Optional[str] = None


class AIModelResponse(AIModelBase):
    """AI model response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: ModelStatus
    is_default: bool
    created_at: str


class AIModelPublic(BaseModel):
    """Public AI model info (for /v1/models endpoint)."""
    id: str
    object: str = "model"
    created: int
    owned_by: str
