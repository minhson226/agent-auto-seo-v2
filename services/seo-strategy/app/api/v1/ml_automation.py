"""API endpoints for ML-powered SEO automation features."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user_id
from app.ml.clustering import get_keyword_clusterer
from app.ml.predictor import get_ranking_predictor
from app.ml.content_plan_generator import get_content_plan_generator

router = APIRouter(prefix="/ml", tags=["ML Automation"])


# Request/Response Schemas


class ClusterTfidfRequest(BaseModel):
    """Request for TF-IDF clustering."""

    keywords: List[str] = Field(..., min_length=2, description="Keywords to cluster")
    n_clusters: int = Field(default=5, ge=2, le=20, description="Number of clusters")


class ClusterSemanticRequest(BaseModel):
    """Request for semantic clustering."""

    keywords: List[str] = Field(..., min_length=2, description="Keywords to cluster")
    threshold: float = Field(
        default=0.3, ge=0.1, le=0.9, description="Distance threshold for DBSCAN"
    )
    min_samples: int = Field(default=2, ge=1, le=10, description="Minimum cluster size")


class ClusterResponse(BaseModel):
    """Response for clustering operations."""

    labels: List[int]
    clusters: Dict[str, List[str]]
    n_clusters: Optional[int] = None
    n_noise: Optional[int] = None
    centroids: Optional[List[List[str]]] = None


class SimilarKeywordsRequest(BaseModel):
    """Request for finding similar keywords."""

    query: str = Field(..., description="Query keyword")
    keywords: List[str] = Field(..., min_length=1, description="Keywords to search")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    threshold: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Minimum similarity"
    )


class SimilarKeywordsResponse(BaseModel):
    """Response for similar keywords search."""

    query: str
    similar: List[Dict[str, Any]]


class RankingPredictionRequest(BaseModel):
    """Request for ranking prediction."""

    keyword_difficulty: float = Field(default=50, ge=0, le=100)
    search_volume: int = Field(default=500, ge=0)
    competition: float = Field(default=0.5, ge=0, le=1)
    content_word_count: int = Field(default=1500, ge=0)
    domain_authority: float = Field(default=30, ge=0, le=100)
    backlink_count: int = Field(default=0, ge=0)
    content_quality_score: float = Field(default=70, ge=0, le=100)
    avg_competitor_word_count: int = Field(default=1500, ge=0)
    avg_competitor_da: float = Field(default=50, ge=0, le=100)


class RankingPredictionResponse(BaseModel):
    """Response for ranking prediction."""

    probability: float
    prediction: int
    will_rank: bool
    confidence: float


class ContentPlanGenerateRequest(BaseModel):
    """Request for auto content plan generation."""

    cluster_id: UUID
    workspace_id: UUID
    keywords: List[str] = Field(..., min_length=1)
    primary_keyword: str
    keyword_difficulty: float = Field(default=50, ge=0, le=100)
    search_volume: int = Field(default=500, ge=0)
    competition: float = Field(default=0.5, ge=0, le=1)
    competitor_avg_word_count: Optional[int] = None
    competitor_headings: Optional[List[str]] = None


class ContentPlanResponse(BaseModel):
    """Response for content plan generation."""

    id: str
    cluster_id: str
    workspace_id: str
    title: str
    primary_keyword: str
    target_keywords: List[str]
    priority: str
    status: str
    content_type: str
    estimated_word_count: int
    title_suggestions: List[str]
    outline: List[Dict[str, Any]]
    competitors_data: Dict[str, Any]
    seo_recommendations: List[Dict[str, str]]


# Endpoints


@router.post(
    "/cluster/tfidf",
    response_model=ClusterResponse,
    summary="Cluster keywords using TF-IDF",
)
async def cluster_keywords_tfidf(
    request: ClusterTfidfRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Cluster keywords using TF-IDF vectorization and K-Means.

    Useful for grouping similar keywords based on text similarity.
    """
    clusterer = get_keyword_clusterer(use_semantic=False)

    try:
        result = clusterer.cluster_tfidf(
            keywords=request.keywords,
            n_clusters=request.n_clusters,
        )

        # Convert cluster keys to strings for JSON serialization
        clusters = {str(k): v for k, v in result["clusters"].items()}

        return ClusterResponse(
            labels=result["labels"],
            clusters=clusters,
            n_clusters=len(clusters),
            centroids=result.get("centroids"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clustering failed: {str(e)}",
        )


@router.post(
    "/cluster/semantic",
    response_model=ClusterResponse,
    summary="Cluster keywords using semantic embeddings",
)
async def cluster_keywords_semantic(
    request: ClusterSemanticRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Cluster keywords using SBERT embeddings and DBSCAN.

    Better for understanding semantic meaning and grouping related concepts.
    """
    clusterer = get_keyword_clusterer(use_semantic=True)

    try:
        result = clusterer.cluster_semantic(
            keywords=request.keywords,
            threshold=request.threshold,
            min_samples=request.min_samples,
        )

        # Convert cluster keys to strings for JSON serialization
        clusters = {str(k): v for k, v in result["clusters"].items()}

        return ClusterResponse(
            labels=result["labels"],
            clusters=clusters,
            n_clusters=result.get("n_clusters", len(clusters)),
            n_noise=result.get("n_noise", 0),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic clustering failed: {str(e)}",
        )


@router.post(
    "/similar-keywords",
    response_model=SimilarKeywordsResponse,
    summary="Find similar keywords",
)
async def find_similar_keywords(
    request: SimilarKeywordsRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Find keywords most similar to a query using semantic embeddings."""
    clusterer = get_keyword_clusterer(use_semantic=True)

    try:
        similar = clusterer.find_similar_keywords(
            query=request.query,
            keywords=request.keywords,
            top_k=request.top_k,
            threshold=request.threshold,
        )

        return SimilarKeywordsResponse(
            query=request.query,
            similar=[{"keyword": kw, "similarity": score} for kw, score in similar],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similarity search failed: {str(e)}",
        )


@router.post(
    "/predict-ranking",
    response_model=RankingPredictionResponse,
    summary="Predict ranking probability",
)
async def predict_ranking(
    request: RankingPredictionRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Predict the probability of ranking in top 10 search results.

    Uses a combination of keyword metrics and content signals to predict
    ranking potential.
    """
    predictor = get_ranking_predictor()

    try:
        result = predictor.predict_from_dict(request.model_dump())

        return RankingPredictionResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@router.post(
    "/generate-content-plan",
    response_model=ContentPlanResponse,
    summary="Auto-generate content plan",
)
async def generate_content_plan(
    request: ContentPlanGenerateRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Automatically generate a content plan for a keyword cluster.

    Creates an optimized content plan with:
    - Title suggestions
    - Content outline
    - Word count recommendations
    - SEO recommendations
    """
    generator = get_content_plan_generator()

    try:
        keyword_metrics = {
            "difficulty": request.keyword_difficulty,
            "volume": request.search_volume,
            "competition": request.competition,
        }

        competitor_data = {
            "avg_word_count": request.competitor_avg_word_count,
            "common_headings": request.competitor_headings or [],
        }

        plan = generator.generate_content_plan(
            cluster_id=request.cluster_id,
            workspace_id=request.workspace_id,
            keywords=request.keywords,
            primary_keyword=request.primary_keyword,
            keyword_metrics=keyword_metrics,
            competitor_data=competitor_data,
        )

        return ContentPlanResponse(**plan)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content plan generation failed: {str(e)}",
        )


@router.get(
    "/feature-importance",
    summary="Get ranking predictor feature importance",
)
async def get_feature_importance(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get the feature importance scores from the ranking predictor.

    Only available after the model has been trained.
    """
    predictor = get_ranking_predictor()
    importance = predictor.get_feature_importance()

    if importance is None:
        return {
            "message": "Model not trained yet. Using heuristic predictions.",
            "feature_names": predictor.FEATURE_NAMES,
        }

    return {
        "feature_importance": importance,
        "feature_names": predictor.FEATURE_NAMES,
    }
