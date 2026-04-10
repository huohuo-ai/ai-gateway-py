"""AI Model service."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ModelStatus
from app.core.exceptions import ModelNotFoundError
from app.models import AIModel
from app.schemas import AIModelCreate, AIModelUpdate


class AIModelService:
    """AI Model management service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, model_id: int) -> Optional[AIModel]:
        """Get model by ID."""
        result = await self.db.execute(
            select(AIModel).where(AIModel.id == model_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[AIModel]:
        """Get model by name."""
        result = await self.db.execute(
            select(AIModel).where(AIModel.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_model_id(self, model_id: str) -> Optional[AIModel]:
        """Get model by model_id (actual API model ID)."""
        result = await self.db.execute(
            select(AIModel).where(AIModel.model_id == model_id)
        )
        return result.scalar_one_or_none()
    
    async def get_default_model(self) -> Optional[AIModel]:
        """Get default active model."""
        result = await self.db.execute(
            select(AIModel)
            .where(AIModel.is_default == True)
            .where(AIModel.status == ModelStatus.ACTIVE)
        )
        return result.scalar_one_or_none()
    
    async def create(self, data: AIModelCreate) -> AIModel:
        """Create new model."""
        # If this is set as default, unset others
        if data.is_default:
            await self._unset_default_models()
        
        model = AIModel(
            name=data.name,
            model_id=data.model_id,
            provider=data.provider,
            base_url=data.base_url,
            api_key=data.api_key,
            status=ModelStatus.ACTIVE,
            is_default=data.is_default,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            timeout=data.timeout,
            system_prompt=data.system_prompt,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model
    
    async def update(self, model_id: int, data: AIModelUpdate) -> AIModel:
        """Update model."""
        model = await self.get_by_id(model_id)
        if not model:
            raise ModelNotFoundError(f"Model {model_id} not found")
        
        # If setting as default, unset others
        if data.is_default:
            await self._unset_default_models()
        
        # Update fields
        if data.name is not None:
            model.name = data.name
        if data.model_id is not None:
            model.model_id = data.model_id
        if data.provider is not None:
            model.provider = data.provider
        if data.base_url is not None:
            model.base_url = data.base_url
        if data.api_key is not None:
            model.api_key = data.api_key
        if data.status is not None:
            model.status = data.status
        if data.is_default is not None:
            model.is_default = data.is_default
        if data.temperature is not None:
            model.temperature = data.temperature
        if data.max_tokens is not None:
            model.max_tokens = data.max_tokens
        if data.timeout is not None:
            model.timeout = data.timeout
        if data.system_prompt is not None:
            model.system_prompt = data.system_prompt
        
        await self.db.commit()
        await self.db.refresh(model)
        return model
    
    async def delete(self, model_id: int) -> None:
        """Delete model."""
        model = await self.get_by_id(model_id)
        if not model:
            raise ModelNotFoundError(f"Model {model_id} not found")
        
        await self.db.delete(model)
        await self.db.commit()
    
    async def list_models(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ModelStatus] = None
    ) -> tuple[list[AIModel], int]:
        """List models with pagination."""
        query = select(AIModel)
        
        if status:
            query = query.where(AIModel.status == status)
        
        # Get total count
        count_result = await self.db.execute(
            select(AIModel).with_only_columns(AIModel.id)
        )
        total = len(count_result.all())
        
        # Get paginated results
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        models = result.scalars().all()
        
        return list(models), total
    
    async def get_active_models(self) -> list[AIModel]:
        """Get all active models."""
        result = await self.db.execute(
            select(AIModel).where(AIModel.status == ModelStatus.ACTIVE)
        )
        return list(result.scalars().all())
    
    async def _unset_default_models(self) -> None:
        """Unset default flag from all models."""
        result = await self.db.execute(
            select(AIModel).where(AIModel.is_default == True)
        )
        models = result.scalars().all()
        for model in models:
            model.is_default = False
        await self.db.commit()
