"""Schemas module initialization."""

from app.core.constants import DEFAULT_CHECKLIST
from app.schemas.seo_score import (
    SeoScoreCreate,
    SeoScoreUpdate,
    SeoScoreResponse,
    PaginatedSeoScoreResponse,
    ScoreCalculationResponse,
)

__all__ = [
    "SeoScoreCreate",
    "SeoScoreUpdate",
    "SeoScoreResponse",
    "PaginatedSeoScoreResponse",
    "ScoreCalculationResponse",
    "DEFAULT_CHECKLIST",
]
