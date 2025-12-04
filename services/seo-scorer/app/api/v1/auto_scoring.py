"""Auto Scoring API endpoints.

PHASE-010: SEO Scoring Automation & Self-Correction
"""

import logging
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.seo_score import (
    AutoScoreRequest,
    AutoScoreResponse,
    CorrectionRequest,
    CorrectionResponse,
    DetailedScoreResponse,
    HTMLAnalysisResult,
    ScoreBreakdownItem,
)
from app.services.html_analyzer import HTMLAnalyzer
from app.services.auto_scorer import AutoScorer
from app.services.corrector import TacticalCorrector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auto-score", tags=["Auto Scoring"])


@router.post("", response_model=AutoScoreResponse)
async def auto_score(
    request: AutoScoreRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Automatically analyze and score HTML content for SEO.

    This endpoint analyzes the provided HTML content for SEO factors
    and returns a detailed score with suggestions for improvement.
    """
    # Analyze HTML
    analyzer = HTMLAnalyzer()
    analysis = analyzer.analyze(request.html_content, request.target_keywords)

    # Score the analysis
    scorer = AutoScorer()
    detailed_score = scorer.get_detailed_score(analysis)

    # Identify issues and get suggestions
    issues = scorer.identify_issues(analysis)
    suggestions = scorer.get_correction_suggestions(issues)

    # Build response
    analysis_result = HTMLAnalysisResult(**analysis)

    breakdown = {}
    for key, value in detailed_score["breakdown"].items():
        breakdown[key] = ScoreBreakdownItem(**value)

    detailed_response = DetailedScoreResponse(
        score=detailed_score["score"],
        total_points=detailed_score["total_points"],
        max_points=detailed_score["max_points"],
        breakdown=breakdown,
        status=detailed_score["status"],
    )

    return AutoScoreResponse(
        score=detailed_score["score"],
        status=detailed_score["status"],
        analysis=analysis_result,
        detailed_score=detailed_response,
        issues=issues,
        suggestions=suggestions,
    )


@router.post("/analyze", response_model=HTMLAnalysisResult)
async def analyze_html(
    request: AutoScoreRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Analyze HTML content for SEO factors without scoring.

    Returns detailed analysis of SEO factors present in the HTML.
    """
    analyzer = HTMLAnalyzer()
    analysis = analyzer.analyze(request.html_content, request.target_keywords)
    return HTMLAnalysisResult(**analysis)


@router.post("/score", response_model=DetailedScoreResponse)
async def score_analysis(
    analysis: Dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Score a pre-analyzed HTML result.

    Use this endpoint when you already have analysis results
    and just need to calculate the score.
    """
    scorer = AutoScorer()
    detailed_score = scorer.get_detailed_score(analysis)

    breakdown = {}
    for key, value in detailed_score["breakdown"].items():
        breakdown[key] = ScoreBreakdownItem(**value)

    return DetailedScoreResponse(
        score=detailed_score["score"],
        total_points=detailed_score["total_points"],
        max_points=detailed_score["max_points"],
        breakdown=breakdown,
        status=detailed_score["status"],
    )


@router.post("/correct", response_model=CorrectionResponse)
async def correct_article(
    request: CorrectionRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Evaluate and potentially trigger correction for an article.

    Analyzes the HTML content and if the score is below 80,
    triggers a correction request for regeneration.
    """
    corrector = TacticalCorrector()

    result = await corrector.evaluate_and_correct(
        article_id=request.article_id,
        html_content=request.html_content,
        target_keywords=request.target_keywords,
        workspace_id=request.workspace_id,
        correction_attempt=request.correction_attempt,
    )

    return CorrectionResponse(
        action=result.get("action", "unknown"),
        article_id=result.get("article_id", request.article_id),
        score=result.get("score", 0),
        issues=result.get("issues", []),
        correction_instructions=result.get("correction_instructions", []),
        correction_attempt=result.get("correction_attempt", 0),
        message=result.get("message", ""),
    )


@router.get("/weights")
async def get_default_weights(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get the default scoring weights.

    Returns the default weights used for SEO scoring.
    """
    return {
        "weights": AutoScorer.DEFAULT_WEIGHTS,
        "threshold_approved": AutoScorer.THRESHOLD_APPROVED,
        "threshold_needs_review": AutoScorer.THRESHOLD_NEEDS_REVIEW,
    }


@router.post("/score-with-weights", response_model=DetailedScoreResponse)
async def score_with_custom_weights(
    analysis: Dict,
    weights: Dict[str, int],
    current_user: CurrentUser = Depends(get_current_user),
):
    """Score analysis with custom weights.

    Allows scoring with workspace-specific or custom weights.
    """
    scorer = AutoScorer(weights=weights)
    detailed_score = scorer.get_detailed_score(analysis)

    breakdown = {}
    for key, value in detailed_score["breakdown"].items():
        breakdown[key] = ScoreBreakdownItem(**value)

    return DetailedScoreResponse(
        score=detailed_score["score"],
        total_points=detailed_score["total_points"],
        max_points=detailed_score["max_points"],
        breakdown=breakdown,
        status=detailed_score["status"],
    )
