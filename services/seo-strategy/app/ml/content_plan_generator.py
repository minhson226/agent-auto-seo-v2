"""Auto content plan generator based on clustering and competitor analysis."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class ContentPlanGenerator:
    """Generates content plans automatically based on keyword clusters and competitor data.

    Analyzes clustered keywords and SERP competitor data to generate
    optimized content plans with suggested titles, word counts, and outlines.
    """

    # Priority thresholds based on difficulty and volume
    PRIORITY_RULES = {
        "high": {
            "difficulty_max": 40,
            "volume_min": 1000,
        },
        "medium": {
            "difficulty_max": 60,
            "volume_min": 500,
        },
        "low": {
            "difficulty_max": 100,
            "volume_min": 0,
        },
    }

    # Word count recommendations based on content type
    WORD_COUNT_TEMPLATES = {
        "blog_post": {"min": 1500, "max": 2500, "avg": 2000},
        "pillar_content": {"min": 3000, "max": 5000, "avg": 4000},
        "listicle": {"min": 1000, "max": 2000, "avg": 1500},
        "how_to_guide": {"min": 2000, "max": 3500, "avg": 2500},
        "product_review": {"min": 1500, "max": 2500, "avg": 2000},
        "comparison": {"min": 2000, "max": 3000, "avg": 2500},
    }

    def __init__(self):
        """Initialize the content plan generator."""
        pass

    def determine_priority(
        self,
        keyword_difficulty: float,
        search_volume: int,
        competition: float = 0.5,
    ) -> str:
        """Determine content priority based on keyword metrics.

        Uses a rule-based approach considering:
        - Lower difficulty = easier to rank = higher priority
        - Higher volume = more traffic potential = higher priority
        - Lower competition = easier to rank = higher priority

        Args:
            keyword_difficulty: 0-100 difficulty score
            search_volume: Monthly search volume
            competition: 0-1 competition level

        Returns:
            Priority level: "high", "medium", or "low"
        """
        # Adjust difficulty based on competition
        adjusted_difficulty = keyword_difficulty * (0.5 + competition * 0.5)

        # Calculate opportunity score
        opportunity_score = search_volume / max(adjusted_difficulty, 1)

        if adjusted_difficulty <= 40 and search_volume >= 1000:
            return "high"
        elif adjusted_difficulty <= 60 and search_volume >= 500:
            return "medium"
        elif opportunity_score >= 20:  # High volume relative to difficulty
            return "medium"
        else:
            return "low"

    def suggest_content_type(
        self,
        keywords: List[str],
        primary_keyword: str,
    ) -> str:
        """Suggest content type based on keywords.

        Analyzes keyword patterns to determine the best content format.

        Args:
            keywords: List of related keywords
            primary_keyword: The main target keyword

        Returns:
            Content type suggestion
        """
        combined = " ".join(keywords + [primary_keyword]).lower()

        # Pattern matching for content type detection
        if any(
            pattern in combined
            for pattern in ["how to", "guide", "tutorial", "step by step"]
        ):
            return "how_to_guide"

        if any(pattern in combined for pattern in ["best", "top", "list", "examples"]):
            return "listicle"

        if any(pattern in combined for pattern in ["vs", "versus", "comparison", "compare"]):
            return "comparison"

        if any(pattern in combined for pattern in ["review", "reviews"]):
            return "product_review"

        if len(keywords) > 10:  # Many related keywords = pillar opportunity
            return "pillar_content"

        return "blog_post"

    def estimate_word_count(
        self,
        content_type: str,
        competitor_avg_word_count: Optional[int] = None,
    ) -> int:
        """Estimate optimal word count for content.

        Args:
            content_type: Type of content to create
            competitor_avg_word_count: Average word count of top competitors

        Returns:
            Recommended word count
        """
        template = self.WORD_COUNT_TEMPLATES.get(
            content_type,
            self.WORD_COUNT_TEMPLATES["blog_post"],
        )

        if competitor_avg_word_count:
            # Aim for 20% more than competitor average
            target = int(competitor_avg_word_count * 1.2)
            # Clamp to template range
            return max(template["min"], min(target, template["max"]))

        return template["avg"]

    def generate_title_suggestions(
        self,
        primary_keyword: str,
        content_type: str,
        count: int = 3,
    ) -> List[str]:
        """Generate title suggestions for content.

        Args:
            primary_keyword: Main target keyword
            content_type: Type of content
            count: Number of suggestions to generate

        Returns:
            List of title suggestions
        """
        suggestions = []

        # Template-based title generation
        templates = {
            "how_to_guide": [
                f"How to {primary_keyword.title()}: A Complete Guide",
                f"The Ultimate Guide to {primary_keyword.title()}",
                f"{primary_keyword.title()}: Step-by-Step Tutorial",
            ],
            "listicle": [
                f"Top 10 {primary_keyword.title()} Tips for Success",
                f"Best {primary_keyword.title()} Strategies in 2024",
                f"15 {primary_keyword.title()} Examples That Work",
            ],
            "comparison": [
                f"{primary_keyword.title()}: Complete Comparison Guide",
                f"Comparing {primary_keyword.title()}: Which is Best?",
                f"{primary_keyword.title()} Face-Off: Detailed Analysis",
            ],
            "product_review": [
                f"{primary_keyword.title()} Review: Honest Assessment",
                f"Is {primary_keyword.title()} Worth It? Full Review",
                f"{primary_keyword.title()}: Pros, Cons & Our Verdict",
            ],
            "pillar_content": [
                f"The Complete {primary_keyword.title()} Resource",
                f"Everything You Need to Know About {primary_keyword.title()}",
                f"{primary_keyword.title()}: Comprehensive Guide for Beginners",
            ],
            "blog_post": [
                f"Understanding {primary_keyword.title()}: What You Need to Know",
                f"{primary_keyword.title()}: Key Insights and Tips",
                f"Mastering {primary_keyword.title()} in Simple Steps",
            ],
        }

        type_templates = templates.get(content_type, templates["blog_post"])
        suggestions = type_templates[:count]

        return suggestions

    def generate_outline(
        self,
        primary_keyword: str,
        related_keywords: List[str],
        content_type: str,
        competitor_headings: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate content outline with suggested headings.

        Args:
            primary_keyword: Main target keyword
            related_keywords: Related keywords to cover
            content_type: Type of content
            competitor_headings: Headings from competitor analysis

        Returns:
            List of outline sections with suggested headings
        """
        outline = []

        # Introduction section
        outline.append({
            "type": "h2",
            "heading": f"What is {primary_keyword.title()}?",
            "description": "Introduction and overview",
            "estimated_words": 200,
        })

        # Core content sections based on related keywords
        for idx, keyword in enumerate(related_keywords[:5]):
            outline.append({
                "type": "h2",
                "heading": keyword.title(),
                "description": f"Section covering {keyword}",
                "estimated_words": 300,
            })

        # Content type specific sections
        if content_type == "how_to_guide":
            outline.append({
                "type": "h2",
                "heading": "Step-by-Step Instructions",
                "description": "Detailed walkthrough",
                "estimated_words": 500,
            })
            outline.append({
                "type": "h2",
                "heading": "Common Mistakes to Avoid",
                "description": "Tips for success",
                "estimated_words": 200,
            })

        elif content_type == "listicle":
            outline.append({
                "type": "h2",
                "heading": "Bonus Tips",
                "description": "Additional recommendations",
                "estimated_words": 200,
            })

        elif content_type == "comparison":
            outline.append({
                "type": "h2",
                "heading": "Head-to-Head Comparison",
                "description": "Detailed feature comparison",
                "estimated_words": 400,
            })
            outline.append({
                "type": "h2",
                "heading": "Which Should You Choose?",
                "description": "Recommendation based on use case",
                "estimated_words": 200,
            })

        # Conclusion
        outline.append({
            "type": "h2",
            "heading": "Conclusion",
            "description": "Summary and call to action",
            "estimated_words": 150,
        })

        # FAQ section
        outline.append({
            "type": "h2",
            "heading": "Frequently Asked Questions",
            "description": "Address common questions",
            "estimated_words": 200,
        })

        return outline

    def generate_content_plan(
        self,
        cluster_id: UUID,
        workspace_id: UUID,
        keywords: List[str],
        primary_keyword: str,
        keyword_metrics: Optional[Dict[str, Any]] = None,
        competitor_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a complete content plan for a keyword cluster.

        Args:
            cluster_id: ID of the keyword cluster
            workspace_id: Workspace ID
            keywords: List of keywords in the cluster
            primary_keyword: Main target keyword
            keyword_metrics: Metrics like difficulty, volume, competition
            competitor_data: Data from competitor analysis

        Returns:
            Complete content plan dictionary
        """
        metrics = keyword_metrics or {}
        competitors = competitor_data or {}

        # Determine priority
        priority = self.determine_priority(
            keyword_difficulty=metrics.get("difficulty", 50),
            search_volume=metrics.get("volume", 500),
            competition=metrics.get("competition", 0.5),
        )

        # Suggest content type
        content_type = self.suggest_content_type(keywords, primary_keyword)

        # Estimate word count
        competitor_avg = competitors.get("avg_word_count")
        estimated_word_count = self.estimate_word_count(content_type, competitor_avg)

        # Generate title suggestions
        title_suggestions = self.generate_title_suggestions(
            primary_keyword,
            content_type,
            count=3,
        )

        # Generate outline
        competitor_headings = competitors.get("common_headings", [])
        outline = self.generate_outline(
            primary_keyword,
            keywords[:5],  # Use top 5 related keywords
            content_type,
            competitor_headings,
        )

        # Build the content plan
        content_plan = {
            "id": str(uuid4()),
            "cluster_id": str(cluster_id),
            "workspace_id": str(workspace_id),
            "title": title_suggestions[0] if title_suggestions else primary_keyword.title(),
            "primary_keyword": primary_keyword,
            "target_keywords": keywords,
            "priority": priority,
            "status": "draft",
            "content_type": content_type,
            "estimated_word_count": estimated_word_count,
            "title_suggestions": title_suggestions,
            "outline": outline,
            "competitors_data": {
                "avg_word_count": competitor_avg,
                "common_headings": competitor_headings,
                "analyzed_urls": competitors.get("analyzed_urls", []),
            },
            "seo_recommendations": self._generate_seo_recommendations(
                primary_keyword,
                keywords,
                estimated_word_count,
                metrics,
            ),
        }

        return content_plan

    def _generate_seo_recommendations(
        self,
        primary_keyword: str,
        keywords: List[str],
        word_count: int,
        metrics: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Generate SEO recommendations for the content plan.

        Args:
            primary_keyword: Main target keyword
            keywords: Related keywords
            word_count: Estimated word count
            metrics: Keyword metrics

        Returns:
            List of SEO recommendations
        """
        recommendations = []

        # Title tag recommendation
        recommendations.append({
            "type": "title_tag",
            "recommendation": f"Include '{primary_keyword}' in the first 60 characters",
            "priority": "high",
        })

        # Meta description
        recommendations.append({
            "type": "meta_description",
            "recommendation": f"Write a compelling 150-160 character meta description with '{primary_keyword}'",
            "priority": "high",
        })

        # Header structure
        recommendations.append({
            "type": "headers",
            "recommendation": f"Use H1 with '{primary_keyword}', H2s for main sections, H3s for subsections",
            "priority": "high",
        })

        # Keyword density
        target_occurrences = word_count // 200  # Roughly 0.5% density
        recommendations.append({
            "type": "keyword_usage",
            "recommendation": f"Use '{primary_keyword}' approximately {target_occurrences} times naturally",
            "priority": "medium",
        })

        # Internal linking
        recommendations.append({
            "type": "internal_links",
            "recommendation": "Add 3-5 relevant internal links to related content",
            "priority": "medium",
        })

        # Related keywords
        if len(keywords) > 1:
            related = ", ".join(keywords[1:4])
            recommendations.append({
                "type": "related_keywords",
                "recommendation": f"Naturally incorporate related terms: {related}",
                "priority": "medium",
            })

        return recommendations

    def generate_batch_content_plans(
        self,
        clusters: List[Dict[str, Any]],
        workspace_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Generate content plans for multiple clusters.

        Args:
            clusters: List of cluster dictionaries with keywords and metrics
            workspace_id: Workspace ID

        Returns:
            List of generated content plans
        """
        plans = []

        for cluster in clusters:
            cluster_id = UUID(cluster.get("id", str(uuid4())))
            keywords = cluster.get("keywords", [])
            primary = cluster.get("primary_keyword", keywords[0] if keywords else "")

            if not primary:
                continue

            plan = self.generate_content_plan(
                cluster_id=cluster_id,
                workspace_id=workspace_id,
                keywords=keywords,
                primary_keyword=primary,
                keyword_metrics=cluster.get("metrics"),
                competitor_data=cluster.get("competitor_data"),
            )
            plans.append(plan)

        return plans


# Singleton instance
_content_plan_generator: Optional[ContentPlanGenerator] = None


def get_content_plan_generator() -> ContentPlanGenerator:
    """Get or create the content plan generator instance.

    Returns:
        ContentPlanGenerator instance
    """
    global _content_plan_generator
    if _content_plan_generator is None:
        _content_plan_generator = ContentPlanGenerator()
    return _content_plan_generator
