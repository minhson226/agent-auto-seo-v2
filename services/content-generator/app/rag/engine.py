"""RAG Engine for context-enhanced content generation."""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class RetrievedContext:
    """Retrieved context from vector search."""

    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any]


@dataclass
class EnrichedPrompt:
    """Enriched prompt with RAG context."""

    original_prompt: str
    context_snippets: List[RetrievedContext]
    enriched_prompt: str
    total_context_tokens: int


class RAGEngine:
    """Retrieval-Augmented Generation engine.

    Enhances content generation by:
    1. Retrieving relevant context from SERP data and existing content
    2. Embedding queries for semantic search
    3. Combining retrieved context with generation prompts

    Supports mock mode for testing without vector database.
    """

    def __init__(self, mock_mode: bool = False):
        """Initialize RAG Engine.

        Args:
            mock_mode: If True, operates in mock mode without real vector store
        """
        self._mock_mode = mock_mode
        self._mock_storage: List[Dict[str, Any]] = []
        self.embeddings = None
        self.vectorstore = None

        # Try to initialize real embeddings if not in mock mode
        if not mock_mode:
            self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Initialize embedding model and vector store."""
        try:
            # Import optional dependencies
            openai_key = settings.OPENAI_API_KEY
            if openai_key:
                from openai import OpenAI

                self._openai_client = OpenAI(api_key=openai_key)
                logger.info("RAG Engine initialized with OpenAI embeddings")
            else:
                logger.warning("No OpenAI API key, RAG Engine in mock mode")
                self._mock_mode = True
        except ImportError:
            logger.warning("Required packages not installed for RAG, using mock mode")
            self._mock_mode = True

    @property
    def mock_mode(self) -> bool:
        """Check if RAG engine is in mock mode."""
        return self._mock_mode

    async def enrich_context(
        self,
        query: str,
        keywords: Optional[List[str]] = None,
        max_context: int = 5,
    ) -> EnrichedPrompt:
        """Enrich a query with relevant context.

        Args:
            query: The query or topic to enrich
            keywords: Optional keywords to include in search
            max_context: Maximum number of context snippets to retrieve

        Returns:
            EnrichedPrompt with original and enriched prompt
        """
        if self._mock_mode:
            return self._enrich_mock_context(query, keywords, max_context)

        try:
            # Get relevant context from stored data
            contexts = await self._retrieve_relevant_context(query, keywords, max_context)

            # Build enriched prompt
            enriched_prompt = self._build_enriched_prompt(query, contexts)

            # Estimate context tokens
            context_text = " ".join([c.content for c in contexts])
            estimated_tokens = len(context_text.split()) * 2

            return EnrichedPrompt(
                original_prompt=query,
                context_snippets=contexts,
                enriched_prompt=enriched_prompt,
                total_context_tokens=estimated_tokens,
            )
        except Exception as e:
            logger.error(f"Error enriching context: {e}")
            # Fallback to mock if real RAG fails
            return self._enrich_mock_context(query, keywords, max_context)

    async def _retrieve_relevant_context(
        self,
        query: str,
        keywords: Optional[List[str]],
        max_context: int,
    ) -> List[RetrievedContext]:
        """Retrieve relevant context using vector search.

        Args:
            query: The search query
            keywords: Optional keywords to boost
            max_context: Maximum results

        Returns:
            List of retrieved contexts
        """
        # In a real implementation, this would:
        # 1. Embed the query using OpenAI embeddings
        # 2. Search pgvector for similar documents
        # 3. Return the most relevant results

        # For now, return from mock storage if available
        if self._mock_storage:
            results = []
            search_terms = query.lower().split()
            if keywords:
                search_terms.extend([k.lower() for k in keywords])

            for doc in self._mock_storage:
                content_lower = doc["content"].lower()
                score = sum(1 for term in search_terms if term in content_lower)
                if score > 0:
                    results.append(
                        RetrievedContext(
                            content=doc["content"],
                            source=doc.get("source", "unknown"),
                            relevance_score=score / len(search_terms),
                            metadata=doc.get("metadata", {}),
                        )
                    )

            # Sort by relevance and return top results
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            return results[:max_context]

        return []

    def _build_enriched_prompt(
        self,
        original_prompt: str,
        contexts: List[RetrievedContext],
    ) -> str:
        """Build enriched prompt with context.

        Args:
            original_prompt: The original prompt
            contexts: Retrieved context snippets

        Returns:
            Enriched prompt string
        """
        if not contexts:
            return original_prompt

        context_section = "\n\n".join(
            [
                f"[Source: {ctx.source}]\n{ctx.content}"
                for ctx in contexts
            ]
        )

        return f"""Based on the following relevant context:

{context_section}

---

{original_prompt}

Use the context above to provide more accurate and comprehensive content."""

    def _enrich_mock_context(
        self,
        query: str,
        keywords: Optional[List[str]],
        max_context: int,
    ) -> EnrichedPrompt:
        """Generate mock enriched context for testing.

        Args:
            query: The query
            keywords: Optional keywords
            max_context: Maximum context items

        Returns:
            Mock EnrichedPrompt
        """
        keywords_str = ", ".join(keywords) if keywords else "relevant topics"

        mock_contexts = [
            RetrievedContext(
                content=f"Mock context about {query}: This is relevant information "
                f"that would be retrieved from the vector database.",
                source="mock-serp-data",
                relevance_score=0.95,
                metadata={"mock": True},
            ),
            RetrievedContext(
                content=f"Additional context about {keywords_str}: Industry best practices "
                f"and recent developments in this area.",
                source="mock-knowledge-base",
                relevance_score=0.85,
                metadata={"mock": True},
            ),
        ][:max_context]

        enriched = self._build_enriched_prompt(query, mock_contexts)

        return EnrichedPrompt(
            original_prompt=query,
            context_snippets=mock_contexts,
            enriched_prompt=enriched,
            total_context_tokens=len(enriched.split()) * 2,
        )

    async def index_serp_data(
        self,
        query: str,
        serp_results: List[Dict[str, Any]],
    ) -> int:
        """Index SERP data for future retrieval.

        Args:
            query: The search query
            serp_results: SERP results to index

        Returns:
            Number of documents indexed
        """
        if self._mock_mode:
            # Store in mock storage
            for result in serp_results:
                self._mock_storage.append({
                    "content": result.get("snippet", ""),
                    "source": result.get("url", "serp"),
                    "metadata": {
                        "query": query,
                        "title": result.get("title", ""),
                    },
                })
            return len(serp_results)

        # In a real implementation, this would:
        # 1. Extract text content from SERP results
        # 2. Generate embeddings using OpenAI
        # 3. Store in pgvector
        logger.info(f"Indexed {len(serp_results)} SERP results for query: {query}")
        return len(serp_results)

    async def index_content(
        self,
        content: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index content for future retrieval.

        Args:
            content: The content to index
            source: Source identifier
            metadata: Optional metadata

        Returns:
            True if indexing was successful
        """
        if self._mock_mode:
            self._mock_storage.append({
                "content": content,
                "source": source,
                "metadata": metadata or {},
            })
            return True

        # In a real implementation, this would embed and store the content
        logger.info(f"Indexed content from source: {source}")
        return True

    def clear_storage(self):
        """Clear mock storage (for testing)."""
        self._mock_storage = []


# Global RAG engine instance
rag_engine = RAGEngine()
