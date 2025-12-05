"""Performance data schemas."""

from datetime import date as date_type
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PerformanceDataInput(BaseModel):
    """Input schema for manual performance data entry."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com/article",
                "date": "2025-11-23",
                "impressions": 1000,
                "clicks": 50,
                "position": 5.2,
                "workspace_id": "123e4567-e89b-12d3-a456-426614174000",
                "article_id": "123e4567-e89b-12d3-a456-426614174001",
            }
        }
    )

    url: str = Field(..., description="URL of the page/article")
    date: date_type = Field(..., description="Date of the performance data")
    impressions: int = Field(ge=0, description="Number of impressions")
    clicks: int = Field(ge=0, description="Number of clicks")
    position: float = Field(ge=0, description="Average search position")
    workspace_id: Optional[str] = Field(default=None, description="Workspace ID")
    article_id: Optional[str] = Field(default=None, description="Article ID")
    ai_model_used: Optional[str] = Field(default=None, description="AI model used for content")
    prompt_id: Optional[str] = Field(default=None, description="Prompt ID used")
    cost_usd: Optional[float] = Field(default=None, ge=0, description="Cost in USD")


class PerformanceDataResponse(BaseModel):
    """Response schema for performance data entry."""

    success: bool
    message: str
    url_hash: str


class ArticlePerformance(BaseModel):
    """Performance data for a specific date."""

    date: str
    impressions: int
    clicks: int
    position: float


class ArticlePerformanceResponse(BaseModel):
    """Response schema for article performance time series."""

    article_id: str
    data: List[ArticlePerformance]


class TopArticle(BaseModel):
    """Top performing article summary."""

    article_id: str
    url: str
    total_impressions: int
    total_clicks: int
    avg_position: float


class SummaryResponse(BaseModel):
    """Response schema for performance summary."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workspace_id": "123e4567-e89b-12d3-a456-426614174000",
                "date_from": "2025-10-24",
                "date_to": "2025-11-23",
                "total_impressions": 10000,
                "total_clicks": 500,
                "avg_position": 8.5,
                "articles_ranking": 25,
                "top_articles": [
                    {
                        "article_id": "article-1",
                        "url": "https://example.com/article-1",
                        "total_impressions": 5000,
                        "total_clicks": 250,
                        "avg_position": 3.5,
                    }
                ],
            }
        }
    )

    workspace_id: str
    date_from: str
    date_to: str
    total_impressions: int
    total_clicks: int
    avg_position: float
    articles_ranking: int
    top_articles: List[TopArticle]
