"""LLM Gateway API endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, get_current_user
from app.llm_gateway import LLMGateway, CostRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM Gateway"])


class GenerateRequest(BaseModel):
    """Request for LLM generation."""

    prompt: str = Field(..., min_length=1, max_length=50000)
    provider: str = Field(default="openai")
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2000, ge=1, le=8000)


class GenerateResponse(BaseModel):
    """Response from LLM generation."""

    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: str


class ModelSelectionRequest(BaseModel):
    """Request for model selection."""

    priority: str = Field(default="medium")
    word_count: Optional[int] = Field(None, ge=100, le=50000)
    max_budget_usd: Optional[float] = Field(None, ge=0.0)


class ModelSelectionResponse(BaseModel):
    """Response from model selection."""

    provider: str
    model: str
    estimated_cost_per_1k_tokens: float
    reason: str


class ProviderInfo(BaseModel):
    """Provider information."""

    name: str
    available: bool
    models: List[str]
    default_model: str


@router.post("/generate", response_model=GenerateResponse)
async def generate_content(
    request: GenerateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate content using LLM Gateway.

    Supports multiple providers: openai, anthropic, google, xai
    """
    gateway = LLMGateway()

    try:
        response = await gateway.generate(
            prompt=request.prompt,
            provider=request.provider,
            model=request.model,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        return GenerateResponse(
            content=response.content,
            model=response.model,
            provider=response.provider,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            total_tokens=response.total_tokens,
            cost_usd=str(response.cost_usd),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content generation failed",
        )


@router.post("/select-model", response_model=ModelSelectionResponse)
async def select_optimal_model(
    request: ModelSelectionRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Select optimal model based on priority and constraints.

    Uses Cost Router to choose the best model for the task.
    """
    cost_router = CostRouter()

    selection = cost_router.get_model_selection(
        priority=request.priority,
        word_count=request.word_count,
        max_budget_usd=request.max_budget_usd,
    )

    return ModelSelectionResponse(
        provider=selection.provider,
        model=selection.model,
        estimated_cost_per_1k_tokens=selection.estimated_cost_per_1k_tokens,
        reason=selection.reason,
    )


@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers(
    current_user: CurrentUser = Depends(get_current_user),
):
    """List all available LLM providers and their models."""
    gateway = LLMGateway()

    providers = []
    for name in gateway.get_all_providers():
        provider = gateway.get_provider(name)
        if provider:
            providers.append(
                ProviderInfo(
                    name=name,
                    available=provider.is_available,
                    models=provider.get_available_models(),
                    default_model=provider.get_default_model(),
                )
            )

    return providers
