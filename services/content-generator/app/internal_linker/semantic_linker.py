"""Semantic Internal Linker using sentence embeddings."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.internal_linker.models import InternalLinkOpportunity, RelatedArticle

logger = logging.getLogger(__name__)

# Maximum content length for embedding to avoid excessive processing
MAX_CONTENT_LENGTH = 1000


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score between 0 and 1
    """
    if not vec1 or not vec2:
        return 0.0

    # Calculate dot product and magnitudes
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


class SemanticInternalLinker:
    """Internal linker using semantic similarity with embeddings.

    Uses sentence-transformers to find semantically related articles
    for internal linking.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        db=None,
        mock_mode: bool = False,
    ):
        """Initialize the Semantic Internal Linker.

        Args:
            model_name: Name of the sentence-transformers model to use
            db: Database session for querying articles
            mock_mode: If True, use mock data for testing
        """
        self.model_name = model_name
        self.db = db
        self._mock_mode = mock_mode
        self._model = None
        self._mock_articles: List[Dict[str, Any]] = []

    @property
    def mock_mode(self) -> bool:
        """Check if linker is in mock mode."""
        return self._mock_mode

    def set_mock_articles(self, articles: List[Dict[str, Any]]) -> None:
        """Set mock articles for testing.

        Args:
            articles: List of article dicts with id, content, embedding
        """
        self._mock_articles = articles

    def _get_model(self):
        """Get or load the sentence transformer model."""
        if self._model is not None:
            return self._model

        if self._mock_mode:
            return None

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded sentence transformer model: {self.model_name}")
            return self._model
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Install it with: pip install sentence-transformers"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            return None

    def encode(self, text: str) -> Optional[List[float]]:
        """Encode text to embedding vector.

        Args:
            text: Text to encode

        Returns:
            Embedding vector or None if encoding fails
        """
        if self._mock_mode:
            # Return a simple mock embedding based on text length
            import hashlib

            hash_val = int(hashlib.sha256(text.encode()).hexdigest(), 16)
            return [(hash_val >> i) % 256 / 256.0 for i in range(384)]

        model = self._get_model()
        if not model:
            return None

        try:
            embedding = model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            return None

    async def get_published_articles_with_embeddings(
        self,
        workspace_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get published articles with embeddings for a workspace.

        Args:
            workspace_id: The workspace ID

        Returns:
            List of article dictionaries with embeddings
        """
        if self._mock_mode:
            return self._mock_articles

        if not self.db:
            return []

        from sqlalchemy import select
        from app.models.article import Article
        from app.models.published_post import PublishedPost

        try:
            query = (
                select(Article)
                .join(PublishedPost, Article.id == PublishedPost.article_id)
                .where(Article.workspace_id == workspace_id)
                .where(Article.status == "published")
            )
            result = await self.db.execute(query)
            articles = result.scalars().all()

            articles_with_embeddings = []
            for article in articles:
                metadata = article.generation_metadata or {}
                embedding = metadata.get("embedding")

                # If no pre-computed embedding, compute it
                if not embedding and article.content:
                    embedding = self.encode(article.content[:MAX_CONTENT_LENGTH])

                articles_with_embeddings.append({
                    "id": article.id,
                    "title": article.title,
                    "content": article.content,
                    "embedding": embedding,
                    "target_keywords": metadata.get("target_keywords", []),
                })

            return articles_with_embeddings
        except Exception as e:
            logger.error(f"Failed to get articles with embeddings: {e}")
            return []

    async def find_related_articles(
        self,
        new_article_id: UUID,
        new_article_content: str,
        workspace_id: UUID,
        threshold: float = 0.7,
        max_results: int = 5,
    ) -> List[RelatedArticle]:
        """Find semantically related articles.

        Args:
            new_article_id: ID of the new article
            new_article_content: Content of the new article
            workspace_id: The workspace ID
            threshold: Minimum similarity score (0-1)
            max_results: Maximum number of results to return

        Returns:
            List of related articles sorted by similarity
        """
        # Encode the new article
        new_embedding = self.encode(new_article_content[:MAX_CONTENT_LENGTH])
        if not new_embedding:
            logger.warning("Failed to encode new article content")
            return []

        # Get existing articles with embeddings
        old_articles = await self.get_published_articles_with_embeddings(workspace_id)

        related = []
        for old in old_articles:
            old_id = old["id"]

            # Skip self
            if old_id == new_article_id:
                continue

            old_embedding = old.get("embedding")
            if not old_embedding:
                continue

            # Calculate similarity
            similarity = cosine_similarity(new_embedding, old_embedding)

            if similarity >= threshold:
                related.append(
                    RelatedArticle(
                        article_id=old_id,
                        title=old.get("title", ""),
                        similarity=similarity,
                        embedding=old_embedding,
                        target_keywords=old.get("target_keywords", []),
                    )
                )

        # Sort by similarity and limit results
        related.sort(key=lambda x: x.similarity, reverse=True)
        return related[:max_results]

    async def find_semantic_link_opportunities(
        self,
        new_article_id: UUID,
        new_article_content: str,
        target_keywords: List[str],
        workspace_id: UUID,
        threshold: float = 0.7,
    ) -> List[InternalLinkOpportunity]:
        """Find link opportunities based on semantic similarity.

        Args:
            new_article_id: ID of the new article
            new_article_content: Content of the new article
            target_keywords: Keywords for anchor text
            workspace_id: The workspace ID
            threshold: Minimum similarity threshold

        Returns:
            List of link opportunities with similarity scores
        """
        related_articles = await self.find_related_articles(
            new_article_id=new_article_id,
            new_article_content=new_article_content,
            workspace_id=workspace_id,
            threshold=threshold,
        )

        opportunities = []
        for related in related_articles:
            # Use the first target keyword or the article title as anchor
            anchor_keyword = (
                related.target_keywords[0]
                if related.target_keywords
                else related.title
            )

            opportunities.append(
                InternalLinkOpportunity(
                    from_article_id=new_article_id,
                    to_article_id=related.article_id,
                    keyword=anchor_keyword,
                    similarity_score=related.similarity,
                )
            )

        logger.info(
            f"Found {len(opportunities)} semantic link opportunities "
            f"for article {new_article_id}"
        )
        return opportunities

    async def process_workspace(
        self,
        workspace_id: UUID,
        threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """Process all articles in a workspace for internal linking.

        Args:
            workspace_id: The workspace ID
            threshold: Similarity threshold

        Returns:
            Dict with processing results
        """
        articles = await self.get_published_articles_with_embeddings(workspace_id)

        total_opportunities = []

        for article in articles:
            opportunities = await self.find_semantic_link_opportunities(
                new_article_id=article["id"],
                new_article_content=article.get("content", ""),
                target_keywords=article.get("target_keywords", []),
                workspace_id=workspace_id,
                threshold=threshold,
            )
            total_opportunities.extend(opportunities)

        return {
            "workspace_id": str(workspace_id),
            "articles_processed": len(articles),
            "opportunities_found": len(total_opportunities),
        }
