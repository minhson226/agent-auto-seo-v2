"""Tactical Corrector for automatic SEO issue correction.

This module provides a correction loop that identifies issues
and triggers re-generation when scores are below threshold.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.constants import (
    AUTO_SCORE_THRESHOLD_APPROVED,
    MAX_CORRECTION_ATTEMPTS,
    RECOMMENDED_WORD_COUNT,
)
from app.services.auto_scorer import AutoScorer
from app.services.event_publisher import event_publisher

logger = logging.getLogger(__name__)


class TacticalCorrector:
    """Tactical corrector for automatic SEO issue correction."""

    def __init__(self, scorer: Optional[AutoScorer] = None):
        """Initialize the tactical corrector.

        Args:
            scorer: Optional AutoScorer instance for scoring.
        """
        self.scorer = scorer or AutoScorer()

    async def correct(
        self,
        article_id: str,
        score_data: Dict[str, Any],
        workspace_id: Optional[UUID] = None,
        correction_attempt: int = 0,
    ) -> Dict[str, Any]:
        """Attempt to correct an article based on score data.

        Args:
            article_id: The article ID to correct.
            score_data: The scoring data including analysis results.
            workspace_id: Optional workspace ID for event publishing.
            correction_attempt: Current correction attempt number.

        Returns:
            Dictionary with correction result.
        """
        score = score_data.get("score", 0)

        # Check if score meets threshold
        if score >= AUTO_SCORE_THRESHOLD_APPROVED:
            logger.info(
                f"Article {article_id} score {score} meets threshold, "
                f"approved for publishing"
            )
            await self._publish_approved_event(article_id, score_data, workspace_id)
            return {
                "action": "approved",
                "article_id": article_id,
                "score": score,
                "message": "Article approved for publishing",
            }

        # Check if max corrections reached
        if correction_attempt >= MAX_CORRECTION_ATTEMPTS:
            logger.warning(
                f"Article {article_id} reached max correction attempts "
                f"({MAX_CORRECTION_ATTEMPTS}), manual review required"
            )
            return {
                "action": "manual_review_required",
                "article_id": article_id,
                "score": score,
                "correction_attempt": correction_attempt,
                "message": "Max correction attempts reached, manual review required",
            }

        # Identify issues from score data
        issues = self._identify_issues(score_data)

        if not issues:
            logger.info(f"Article {article_id} has no identifiable issues to correct")
            return {
                "action": "no_issues_found",
                "article_id": article_id,
                "score": score,
                "message": "No specific issues identified for correction",
            }

        # Generate correction instructions
        correction_instructions = self._generate_correction_instructions(issues)

        logger.info(
            f"Article {article_id} needs correction (score: {score}), "
            f"issues: {issues}, attempt: {correction_attempt + 1}"
        )

        # Publish regeneration request event
        await self._publish_regeneration_event(
            article_id,
            issues,
            correction_instructions,
            workspace_id,
            correction_attempt + 1,
        )

        return {
            "action": "correction_requested",
            "article_id": article_id,
            "score": score,
            "issues": issues,
            "correction_instructions": correction_instructions,
            "correction_attempt": correction_attempt + 1,
            "message": "Correction request sent for regeneration",
        }

    def _identify_issues(self, score_data: Dict[str, Any]) -> List[str]:
        """Identify issues from score data.

        Args:
            score_data: The scoring data.

        Returns:
            List of issue identifiers.
        """
        issues = []

        # Check breakdown if available
        breakdown = score_data.get("breakdown", {})
        for item, data in breakdown.items():
            if isinstance(data, dict) and not data.get("passed", True):
                issue_name = self._factor_to_issue(item)
                if issue_name:
                    issues.append(issue_name)

        # If no breakdown, check analysis directly
        if not issues and "analysis" in score_data:
            analysis = score_data["analysis"]
            issues = self.scorer.identify_issues(analysis)

        return issues

    def _factor_to_issue(self, factor: str) -> Optional[str]:
        """Convert scoring factor to issue name.

        Args:
            factor: The scoring factor name.

        Returns:
            Corresponding issue name or None.
        """
        mapping = {
            "title_contains_keyword": "missing_keyword_in_title",
            "h1_present": "missing_h1",
            "h1_contains_keyword": "missing_keyword_in_h1",
            "h2_contains_keyword": "missing_keyword_in_h2",
            "keyword_density_ok": "keyword_density_issue",
            "images_have_alt": "missing_alt_tags",
            "word_count_adequate": "low_word_count",
            "has_internal_links": "no_internal_links",
            "has_external_links": "no_external_links",
            "meta_description": "missing_meta_description",
        }
        return mapping.get(factor)

    def _generate_correction_instructions(self, issues: List[str]) -> List[str]:
        """Generate correction instructions for identified issues.

        Args:
            issues: List of issue identifiers.

        Returns:
            List of correction instructions.
        """
        instructions_map = {
            "missing_keyword_in_title": (
                "Add main keyword to the page title"
            ),
            "missing_h1": "Add an H1 heading that includes the main keyword",
            "missing_keyword_in_h1": "Include the main keyword in the H1 heading",
            "missing_keyword_in_h2": "Add main keyword to H2 headings",
            "keyword_density_issue": (
                "Adjust keyword usage - aim for 0.5-3% density"
            ),
            "missing_alt_tags": "Add descriptive alt text to all images",
            "low_word_count": f"Expand content to {RECOMMENDED_WORD_COUNT}+ words",
            "no_internal_links": "Add internal links to related content",
            "no_external_links": "Add authoritative external references",
            "missing_meta_description": (
                "Add a meta description (150-160 characters)"
            ),
        }

        return [
            instructions_map.get(issue, f"Fix issue: {issue}")
            for issue in issues
        ]

    async def _publish_approved_event(
        self,
        article_id: str,
        score_data: Dict[str, Any],
        workspace_id: Optional[UUID],
    ):
        """Publish article approved for publishing event.

        Args:
            article_id: The article ID.
            score_data: The scoring data.
            workspace_id: Optional workspace ID.
        """
        try:
            await event_publisher.publish(
                "article.approved_for_publishing",
                {
                    "article_id": article_id,
                    "score": score_data.get("score", 0),
                    "status": "approved",
                },
                workspace_id=workspace_id,
            )
            logger.info(f"Published article.approved_for_publishing for {article_id}")
        except Exception as e:
            logger.warning(f"Failed to publish approved event: {e}")

    async def _publish_regeneration_event(
        self,
        article_id: str,
        issues: List[str],
        correction_instructions: List[str],
        workspace_id: Optional[UUID],
        correction_attempt: int,
    ):
        """Publish article regeneration request event.

        Args:
            article_id: The article ID.
            issues: List of identified issues.
            correction_instructions: List of correction instructions.
            workspace_id: Optional workspace ID.
            correction_attempt: Current correction attempt number.
        """
        try:
            await event_publisher.publish(
                "article.generate.request",
                {
                    "article_id": article_id,
                    "correction_reason": issues,
                    "correction_instructions": correction_instructions,
                    "correction_attempt": correction_attempt,
                },
                workspace_id=workspace_id,
            )
            logger.info(
                f"Published article.generate.request for {article_id} "
                f"(attempt {correction_attempt})"
            )
        except Exception as e:
            logger.warning(f"Failed to publish regeneration event: {e}")

    async def evaluate_and_correct(
        self,
        article_id: str,
        html_content: str,
        target_keywords: List[str],
        workspace_id: Optional[UUID] = None,
        correction_attempt: int = 0,
    ) -> Dict[str, Any]:
        """Evaluate HTML content and trigger correction if needed.

        This is a convenience method that combines analysis, scoring,
        and correction in one call.

        Args:
            article_id: The article ID.
            html_content: The HTML content to analyze.
            target_keywords: Target keywords for analysis.
            workspace_id: Optional workspace ID.
            correction_attempt: Current correction attempt number.

        Returns:
            Dictionary with evaluation and correction result.
        """
        # Import here to avoid circular imports
        from app.services.html_analyzer import HTMLAnalyzer

        analyzer = HTMLAnalyzer()
        analysis = analyzer.analyze(html_content, target_keywords)

        detailed_score = self.scorer.get_detailed_score(analysis)
        detailed_score["analysis"] = analysis

        return await self.correct(
            article_id,
            detailed_score,
            workspace_id,
            correction_attempt,
        )
