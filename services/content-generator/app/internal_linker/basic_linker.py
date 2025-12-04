"""Basic Internal Linker using string matching."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.internal_linker.models import InternalLinkOpportunity

logger = logging.getLogger(__name__)


def _get_target_keywords(article) -> List[str]:
    """Extract target keywords from an article.

    Args:
        article: Article model instance

    Returns:
        List of target keywords
    """
    if not article.generation_metadata:
        return []
    return article.generation_metadata.get("target_keywords", [])


class BasicInternalLinker:
    """Internal linker using basic string matching.

    Finds internal linking opportunities by looking for exact keyword
    matches in existing articles.
    """

    def __init__(self, db=None, mock_mode: bool = False):
        """Initialize the Basic Internal Linker.

        Args:
            db: Database session for querying articles
            mock_mode: If True, use mock data for testing
        """
        self.db = db
        self._mock_mode = mock_mode
        self._mock_articles: List[Dict[str, Any]] = []

    @property
    def mock_mode(self) -> bool:
        """Check if linker is in mock mode."""
        return self._mock_mode

    def set_mock_articles(self, articles: List[Dict[str, Any]]) -> None:
        """Set mock articles for testing.

        Args:
            articles: List of article dicts with id, content, target_keywords
        """
        self._mock_articles = articles

    async def get_published_articles(
        self,
        workspace_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get published articles for a workspace.

        Args:
            workspace_id: The workspace ID

        Returns:
            List of article dictionaries
        """
        if self._mock_mode:
            return self._mock_articles

        if not self.db:
            return []

        from sqlalchemy import select, text
        from app.models.article import Article
        from app.models.published_post import PublishedPost

        try:
            # Get articles that have been published
            query = (
                select(Article)
                .join(PublishedPost, Article.id == PublishedPost.article_id)
                .where(Article.workspace_id == workspace_id)
                .where(Article.status == "published")
            )
            result = await self.db.execute(query)
            articles = result.scalars().all()

            return [
                {
                    "id": article.id,
                    "title": article.title,
                    "content": article.content,
                    "target_keywords": _get_target_keywords(article),
                }
                for article in articles
            ]
        except Exception as e:
            logger.error(f"Failed to get published articles: {e}")
            return []

    async def find_link_opportunities(
        self,
        new_article_id: UUID,
        new_article_content: str,
        target_keywords: List[str],
        workspace_id: UUID,
    ) -> List[InternalLinkOpportunity]:
        """Find internal link opportunities for a new article.

        Searches existing published articles for keyword matches that
        could link to the new article.

        Args:
            new_article_id: ID of the new article
            new_article_content: Content of the new article
            target_keywords: Keywords to search for
            workspace_id: The workspace ID

        Returns:
            List of link opportunities
        """
        old_articles = await self.get_published_articles(workspace_id)
        opportunities = []

        for old in old_articles:
            old_id = old["id"]
            old_content = old.get("content", "")

            # Skip self
            if old_id == new_article_id:
                continue

            if not old_content:
                continue

            # Search for keyword matches
            for keyword in target_keywords:
                matches = self._find_keyword_matches(old_content, keyword)
                for match in matches:
                    opportunities.append(
                        InternalLinkOpportunity(
                            from_article_id=old_id,
                            to_article_id=new_article_id,
                            keyword=keyword,
                            position=match["position"],
                            context=match["context"],
                        )
                    )

        logger.info(
            f"Found {len(opportunities)} link opportunities for article {new_article_id}"
        )
        return opportunities

    def _find_keyword_matches(
        self,
        content: str,
        keyword: str,
    ) -> List[Dict[str, Any]]:
        """Find all occurrences of a keyword in content.

        Args:
            content: The content to search
            keyword: The keyword to find

        Returns:
            List of matches with position and context
        """
        matches = []
        content_lower = content.lower()
        keyword_lower = keyword.lower()

        # Use word boundary matching for more accurate results
        pattern = r"\b" + re.escape(keyword_lower) + r"\b"

        for match in re.finditer(pattern, content_lower):
            position = match.start()
            # Get surrounding context (100 chars before and after)
            start = max(0, position - 100)
            end = min(len(content), position + len(keyword) + 100)
            context = content[start:end]

            matches.append({
                "position": position,
                "context": context,
            })

        return matches

    async def find_reverse_link_opportunities(
        self,
        new_article_id: UUID,
        new_article_content: str,
        workspace_id: UUID,
    ) -> List[InternalLinkOpportunity]:
        """Find opportunities to link FROM the new article TO existing ones.

        Args:
            new_article_id: ID of the new article
            new_article_content: Content of the new article
            workspace_id: The workspace ID

        Returns:
            List of link opportunities
        """
        old_articles = await self.get_published_articles(workspace_id)
        opportunities = []

        for old in old_articles:
            old_id = old["id"]
            old_keywords = old.get("target_keywords", [])

            # Skip self
            if old_id == new_article_id:
                continue

            # Search for keywords from old articles in the new article
            for keyword in old_keywords:
                matches = self._find_keyword_matches(new_article_content, keyword)
                for match in matches:
                    opportunities.append(
                        InternalLinkOpportunity(
                            from_article_id=new_article_id,
                            to_article_id=old_id,
                            keyword=keyword,
                            position=match["position"],
                            context=match["context"],
                        )
                    )

        logger.info(
            f"Found {len(opportunities)} reverse link opportunities for article {new_article_id}"
        )
        return opportunities

    async def get_all_link_opportunities(
        self,
        new_article_id: UUID,
        new_article_content: str,
        target_keywords: List[str],
        workspace_id: UUID,
    ) -> Tuple[List[InternalLinkOpportunity], List[InternalLinkOpportunity]]:
        """Get all link opportunities (both directions) for a new article.

        Args:
            new_article_id: ID of the new article
            new_article_content: Content of the new article
            target_keywords: Keywords for the new article
            workspace_id: The workspace ID

        Returns:
            Tuple of (to_opportunities, from_opportunities)
        """
        to_opportunities = await self.find_link_opportunities(
            new_article_id=new_article_id,
            new_article_content=new_article_content,
            target_keywords=target_keywords,
            workspace_id=workspace_id,
        )

        from_opportunities = await self.find_reverse_link_opportunities(
            new_article_id=new_article_id,
            new_article_content=new_article_content,
            workspace_id=workspace_id,
        )

        return to_opportunities, from_opportunities
