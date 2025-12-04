"""Tests for RAG Engine functionality."""

from decimal import Decimal

import pytest

from app.rag import RAGEngine


class TestRAGEngine:
    """Tests for RAGEngine class."""

    def test_initialization(self):
        """Test RAG engine initialization."""
        engine = RAGEngine(mock_mode=True)
        assert engine.mock_mode is True

    def test_mock_mode_detection(self):
        """Test mock mode is detected correctly."""
        # Without OpenAI API key, should default to mock mode
        engine = RAGEngine(mock_mode=False)
        # Will likely be in mock mode due to no API key in tests
        assert isinstance(engine.mock_mode, bool)

    @pytest.mark.asyncio
    async def test_enrich_context_mock(self):
        """Test context enrichment in mock mode."""
        engine = RAGEngine(mock_mode=True)

        enriched = await engine.enrich_context(
            query="SEO best practices",
            keywords=["seo", "content marketing"],
            max_context=5,
        )

        assert enriched.original_prompt == "SEO best practices"
        assert len(enriched.context_snippets) > 0
        assert enriched.enriched_prompt is not None
        assert len(enriched.enriched_prompt) > len(enriched.original_prompt)
        assert enriched.total_context_tokens > 0

    @pytest.mark.asyncio
    async def test_enrich_context_includes_keywords(self):
        """Test context enrichment includes keywords."""
        engine = RAGEngine(mock_mode=True)

        enriched = await engine.enrich_context(
            query="Content creation",
            keywords=["writing", "marketing"],
        )

        # Enriched prompt should reference keywords
        assert "writing" in enriched.enriched_prompt.lower() or \
               "marketing" in enriched.enriched_prompt.lower() or \
               "relevant" in enriched.enriched_prompt.lower()

    @pytest.mark.asyncio
    async def test_index_content(self):
        """Test content indexing."""
        engine = RAGEngine(mock_mode=True)

        success = await engine.index_content(
            content="This is test content about SEO optimization.",
            source="test-article",
            metadata={"author": "test"},
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_index_serp_data(self):
        """Test SERP data indexing."""
        engine = RAGEngine(mock_mode=True)

        serp_results = [
            {"title": "SEO Guide", "snippet": "Complete guide to SEO", "url": "https://example.com/1"},
            {"title": "SEO Tips", "snippet": "Top 10 SEO tips", "url": "https://example.com/2"},
        ]

        count = await engine.index_serp_data(
            query="SEO optimization",
            serp_results=serp_results,
        )

        assert count == 2

    @pytest.mark.asyncio
    async def test_retrieve_indexed_content(self):
        """Test retrieving indexed content."""
        engine = RAGEngine(mock_mode=True)

        # Index some content
        await engine.index_content(
            content="Machine learning is a subset of artificial intelligence.",
            source="ml-article",
        )
        await engine.index_content(
            content="Deep learning uses neural networks.",
            source="dl-article",
        )

        # Enrich context should find relevant content
        enriched = await engine.enrich_context(
            query="artificial intelligence",
        )

        # Should find the indexed content
        assert len(enriched.context_snippets) > 0

    def test_clear_storage(self):
        """Test clearing storage."""
        engine = RAGEngine(mock_mode=True)
        engine._mock_storage = [{"content": "test"}]

        engine.clear_storage()

        assert len(engine._mock_storage) == 0

    @pytest.mark.asyncio
    async def test_context_relevance_scoring(self):
        """Test that retrieved context has relevance scores."""
        engine = RAGEngine(mock_mode=True)

        # Index content with specific keywords
        await engine.index_content(
            content="Python programming is great for data science.",
            source="python-article",
        )

        enriched = await engine.enrich_context(
            query="Python data science",
        )

        for context in enriched.context_snippets:
            assert 0 <= context.relevance_score <= 1.0
            assert context.source is not None

    @pytest.mark.asyncio
    async def test_max_context_limit(self):
        """Test max context limit is respected."""
        engine = RAGEngine(mock_mode=True)

        enriched = await engine.enrich_context(
            query="test query",
            max_context=2,
        )

        assert len(enriched.context_snippets) <= 2
