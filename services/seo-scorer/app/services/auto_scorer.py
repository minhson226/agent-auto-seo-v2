"""Auto Scorer for SEO analysis results.

This module provides automatic scoring of HTML analysis results
using configurable weights.
"""

from typing import Any, Dict, Optional

from app.core.constants import RECOMMENDED_WORD_COUNT


class AutoScorer:
    """Automatic scorer for SEO analysis results."""

    # Default weights for each SEO factor (out of total)
    DEFAULT_WEIGHTS: Dict[str, int] = {
        "title_contains_keyword": 15,
        "h1_present": 10,
        "h1_contains_keyword": 10,
        "h2_contains_keyword": 5,
        "keyword_density_ok": 10,
        "images_have_alt": 10,
        "word_count_adequate": 10,
        "has_internal_links": 10,
        "has_external_links": 5,
        "meta_description": 15,
    }

    # Score thresholds
    THRESHOLD_APPROVED = 80
    THRESHOLD_NEEDS_REVIEW = 60

    def __init__(self, weights: Optional[Dict[str, int]] = None):
        """Initialize the auto scorer.

        Args:
            weights: Optional custom weights for SEO factors.
        """
        self.weights = weights if weights is not None else self.DEFAULT_WEIGHTS.copy()

    def score(
        self, analysis: Dict[str, Any], weights: Optional[Dict[str, int]] = None
    ) -> int:
        """Calculate SEO score from analysis results.

        Args:
            analysis: Dictionary of SEO analysis results.
            weights: Optional custom weights to override instance weights.

        Returns:
            SEO score as integer (0-100).
        """
        if not analysis:
            return 0

        active_weights = weights if weights is not None else self.weights

        score = 0
        max_score = 0

        for item, weight in active_weights.items():
            max_score += weight

            # Get the value from analysis
            value = analysis.get(item)

            # Score based on value type and truthiness
            if value is True:
                score += weight
            elif isinstance(value, (int, float)) and value > 0:
                # For numeric values, consider them as True
                score += weight

        if max_score == 0:
            return 0

        return int((score / max_score) * 100)

    def get_detailed_score(
        self, analysis: Dict[str, Any], weights: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Get detailed scoring breakdown.

        Args:
            analysis: Dictionary of SEO analysis results.
            weights: Optional custom weights.

        Returns:
            Dictionary with detailed scoring information.
        """
        active_weights = weights if weights is not None else self.weights

        score_breakdown = {}
        total_score = 0
        max_score = 0

        for item, weight in active_weights.items():
            max_score += weight
            value = analysis.get(item)
            passed = value is True or (isinstance(value, (int, float)) and value > 0)

            if passed:
                total_score += weight

            score_breakdown[item] = {
                "value": value,
                "weight": weight,
                "passed": passed,
                "points": weight if passed else 0,
            }

        final_score = int((total_score / max_score) * 100) if max_score > 0 else 0

        return {
            "score": final_score,
            "total_points": total_score,
            "max_points": max_score,
            "breakdown": score_breakdown,
            "status": self._get_status(final_score),
        }

    def _get_status(self, score: int) -> str:
        """Get status based on score.

        Args:
            score: The calculated score.

        Returns:
            Status string.
        """
        if score >= self.THRESHOLD_APPROVED:
            return "approved"
        elif score >= self.THRESHOLD_NEEDS_REVIEW:
            return "needs_review"
        else:
            return "needs_correction"

    def identify_issues(self, analysis: Dict[str, Any]) -> list:
        """Identify issues that need correction.

        Args:
            analysis: Dictionary of SEO analysis results.

        Returns:
            List of issue identifiers.
        """
        issues = []

        # Check each weighted factor
        checks = [
            ("title_contains_keyword", "missing_keyword_in_title"),
            ("h1_present", "missing_h1"),
            ("h1_contains_keyword", "missing_keyword_in_h1"),
            ("h2_contains_keyword", "missing_keyword_in_h2"),
            ("keyword_density_ok", "keyword_density_issue"),
            ("images_have_alt", "missing_alt_tags"),
            ("word_count_adequate", "low_word_count"),
            ("has_internal_links", "no_internal_links"),
            ("has_external_links", "no_external_links"),
            ("meta_description", "missing_meta_description"),
        ]

        for analysis_key, issue_key in checks:
            value = analysis.get(analysis_key)
            if not value or (isinstance(value, (int, float)) and value <= 0):
                issues.append(issue_key)

        # Additional specific checks
        word_count = analysis.get("word_count", 0)
        if word_count < RECOMMENDED_WORD_COUNT:
            if "low_word_count" not in issues:
                issues.append("low_word_count")

        return issues

    def get_correction_suggestions(self, issues: list) -> list:
        """Get correction suggestions for identified issues.

        Args:
            issues: List of issue identifiers.

        Returns:
            List of correction suggestions.
        """
        suggestions_map = {
            "missing_keyword_in_title": "Add the main keyword to the page title",
            "missing_h1": "Add an H1 heading to the page",
            "missing_keyword_in_h1": "Include the main keyword in the H1 heading",
            "missing_keyword_in_h2": "Add the main keyword to H2 headings",
            "keyword_density_issue": "Adjust keyword usage to maintain 0.5-3% density",
            "missing_alt_tags": "Add alt text to all images",
            "low_word_count": f"Expand content to {RECOMMENDED_WORD_COUNT}+ words for better coverage",
            "no_internal_links": "Add internal links to related content",
            "no_external_links": "Add authoritative external references",
            "missing_meta_description": "Add a meta description (150-160 characters)",
        }

        return [
            {"issue": issue, "suggestion": suggestions_map.get(issue, f"Fix: {issue}")}
            for issue in issues
        ]

    @classmethod
    def from_workspace_weights(
        cls, workspace_weights: Optional[Dict[str, int]] = None
    ) -> "AutoScorer":
        """Create an AutoScorer with workspace-specific weights.

        Args:
            workspace_weights: Optional workspace-specific weights.

        Returns:
            Configured AutoScorer instance.
        """
        if workspace_weights:
            # Merge with defaults, workspace weights take precedence
            weights = cls.DEFAULT_WEIGHTS.copy()
            weights.update(workspace_weights)
            return cls(weights=weights)
        return cls()
