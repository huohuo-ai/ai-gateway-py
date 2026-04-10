"""AI Model configuration model."""
from typing import Optional

from sqlalchemy import (
    Boolean,
    Enum,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ModelProvider, ModelStatus
from app.models.base import Base


class AIModel(Base):
    """AI Model configuration."""
    __tablename__ = "ai_models"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Actual model ID used in API calls (e.g., gpt-3.5-turbo)"
    )
    provider: Mapped[ModelProvider] = mapped_column(
        Enum(ModelProvider),
        default=ModelProvider.OPENAI
    )
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Status
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus),
        default=ModelStatus.ACTIVE
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether this is the default model"
    )
    
    # Parameters
    temperature: Mapped[float] = mapped_column(
        Float,
        default=0.7
    )
    max_tokens: Mapped[int] = mapped_column(
        Integer,
        default=2000
    )
    timeout: Mapped[int] = mapped_column(
        Integer,
        default=60,
        comment="Request timeout in seconds"
    )
    
    # System prompt
    system_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="System prompt to prepend to all requests"
    )
    
    def to_public_dict(self) -> dict:
        """Return public information (no sensitive data)."""
        return {
            "id": self.id,
            "name": self.name,
            "model_id": self.model_id,
            "provider": self.provider.value,
            "status": self.status.value,
            "is_default": self.is_default,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @property
    def is_active(self) -> bool:
        """Check if model is active."""
        return self.status == ModelStatus.ACTIVE
    
    def __repr__(self) -> str:
        return f"<AIModel {self.name}>"
