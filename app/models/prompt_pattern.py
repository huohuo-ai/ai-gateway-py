"""Prompt pattern for risk detection."""
from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import PatternType, RiskLevel
from app.models.base import Base


class PromptPattern(Base):
    """Prompt pattern for risk detection."""
    __tablename__ = "prompt_patterns"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pattern: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Regex pattern"
    )
    pattern_type: Mapped[PatternType] = mapped_column(
        Enum(PatternType),
        nullable=False
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel),
        default=RiskLevel.MEDIUM
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
    
    def __repr__(self) -> str:
        return f"<PromptPattern {self.description}>"
