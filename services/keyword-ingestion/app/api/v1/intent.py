"""Intent classification API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, get_current_user
from app.ml import get_intent_classifier
from app.schemas.keyword import (
    BatchClassifyIntentRequest,
    BatchClassifyIntentResponse,
    ClassifyIntentRequest,
    ClassifyIntentResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/keywords", tags=["Intent Classification"])


@router.post("/classify-intent", response_model=ClassifyIntentResponse)
async def classify_intent(
    request: ClassifyIntentRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Classify the search intent of a keyword.

    Returns the predicted intent (informational, commercial,
    navigational, or transactional) with confidence score.
    """
    classifier = get_intent_classifier(use_ml=False)  # Use pattern-based for speed

    try:
        result = await classifier.get_intent_with_confidence(request.keyword)

        return ClassifyIntentResponse(
            keyword=request.keyword,
            intent=result["intent"],
            confidence=result["confidence"],
            all_scores=result["all_scores"],
        )
    except Exception as e:
        logger.error(f"Error classifying intent for '{request.keyword}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify keyword intent: {str(e)}",
        )


@router.post("/classify-intent/batch", response_model=BatchClassifyIntentResponse)
async def classify_intent_batch(
    request: BatchClassifyIntentRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Classify the search intent of multiple keywords.

    Accepts up to 100 keywords and returns intent predictions
    for each with confidence scores.
    """
    if len(request.keywords) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 keywords allowed per batch",
        )

    classifier = get_intent_classifier(use_ml=False)

    try:
        results = await classifier.classify_batch(request.keywords)

        return BatchClassifyIntentResponse(
            results=[
                ClassifyIntentResponse(
                    keyword=r["keyword"],
                    intent=r["intent"],
                    confidence=r["confidence"],
                    all_scores=r["all_scores"],
                )
                for r in results
            ],
            total=len(results),
        )
    except Exception as e:
        logger.error(f"Error classifying intent batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify keyword intents: {str(e)}",
        )
