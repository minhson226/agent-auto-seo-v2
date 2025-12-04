"""RAG API endpoints for context enrichment."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, get_current_user
from app.rag import RAGEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])


class EnrichContextRequest(BaseModel):
    """Request for context enrichment."""

    query: str = Field(..., min_length=1, max_length=5000)
    keywords: Optional[List[str]] = None
    max_context: int = Field(default=5, ge=1, le=20)


class RetrievedContextResponse(BaseModel):
    """Response for a retrieved context snippet."""

    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any]


class EnrichContextResponse(BaseModel):
    """Response for context enrichment."""

    original_prompt: str
    enriched_prompt: str
    context_snippets: List[RetrievedContextResponse]
    total_context_tokens: int


class IndexContentRequest(BaseModel):
    """Request for indexing content."""

    content: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1, max_length=500)
    metadata: Optional[Dict[str, Any]] = None


class IndexSerpRequest(BaseModel):
    """Request for indexing SERP data."""

    query: str = Field(..., min_length=1, max_length=500)
    results: List[Dict[str, Any]]


@router.post("/enrich", response_model=EnrichContextResponse)
async def enrich_context(
    request: EnrichContextRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Enrich a query with relevant context from RAG.

    Retrieves relevant context from indexed SERP data and knowledge base
    to enhance content generation.
    """
    rag_engine = RAGEngine()

    try:
        enriched = await rag_engine.enrich_context(
            query=request.query,
            keywords=request.keywords,
            max_context=request.max_context,
        )

        return EnrichContextResponse(
            original_prompt=enriched.original_prompt,
            enriched_prompt=enriched.enriched_prompt,
            context_snippets=[
                RetrievedContextResponse(
                    content=ctx.content,
                    source=ctx.source,
                    relevance_score=ctx.relevance_score,
                    metadata=ctx.metadata,
                )
                for ctx in enriched.context_snippets
            ],
            total_context_tokens=enriched.total_context_tokens,
        )

    except Exception as e:
        logger.error(f"Context enrichment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Context enrichment failed",
        )


@router.post("/index/content")
async def index_content(
    request: IndexContentRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Index content for future RAG retrieval.

    Adds content to the vector store for semantic search.
    """
    rag_engine = RAGEngine()

    try:
        success = await rag_engine.index_content(
            content=request.content,
            source=request.source,
            metadata=request.metadata,
        )

        if success:
            return {"message": "Content indexed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to index content",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content indexing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content indexing failed",
        )


@router.post("/index/serp")
async def index_serp_data(
    request: IndexSerpRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Index SERP data for RAG retrieval.

    Indexes search engine results for use in content generation.
    """
    rag_engine = RAGEngine()

    try:
        count = await rag_engine.index_serp_data(
            query=request.query,
            serp_results=request.results,
        )

        return {"message": f"Indexed {count} SERP results", "count": count}

    except Exception as e:
        logger.error(f"SERP indexing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SERP indexing failed",
        )
