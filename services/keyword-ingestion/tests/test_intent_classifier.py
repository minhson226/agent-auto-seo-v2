"""Tests for intent classifier."""

import pytest

from app.ml import IntentClassifier, get_intent_classifier


class TestIntentClassifier:
    """Tests for IntentClassifier class."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance without ML (pattern-based only)."""
        return IntentClassifier(use_ml=False)

    @pytest.mark.asyncio
    async def test_classify_informational(self, classifier):
        """Test classification of informational keywords."""
        result = await classifier.classify("how to learn python")

        assert "informational" in result
        assert "commercial" in result
        assert "navigational" in result
        assert "transactional" in result
        assert result["informational"] > 0

    @pytest.mark.asyncio
    async def test_classify_commercial(self, classifier):
        """Test classification of commercial keywords."""
        result = await classifier.classify("best laptop reviews 2024")

        assert result["commercial"] > 0

    @pytest.mark.asyncio
    async def test_classify_transactional(self, classifier):
        """Test classification of transactional keywords."""
        result = await classifier.classify("buy iphone 15 discount")

        assert result["transactional"] > 0

    @pytest.mark.asyncio
    async def test_classify_navigational(self, classifier):
        """Test classification of navigational keywords."""
        result = await classifier.classify("facebook login page")

        assert result["navigational"] > 0

    @pytest.mark.asyncio
    async def test_get_primary_intent_informational(self, classifier):
        """Test getting primary intent for informational query."""
        result = await classifier.get_primary_intent("what is machine learning")

        assert result == "informational"

    @pytest.mark.asyncio
    async def test_get_primary_intent_commercial(self, classifier):
        """Test getting primary intent for commercial query."""
        result = await classifier.get_primary_intent("best seo tools comparison")

        assert result == "commercial"

    @pytest.mark.asyncio
    async def test_get_intent_with_confidence(self, classifier):
        """Test getting intent with confidence score."""
        result = await classifier.get_intent_with_confidence("how to cook pasta")

        assert "intent" in result
        assert "confidence" in result
        assert "all_scores" in result
        assert result["intent"] == "informational"
        assert 0 <= result["confidence"] <= 100

    @pytest.mark.asyncio
    async def test_classify_batch(self, classifier):
        """Test batch classification."""
        keywords = [
            "how to learn python",
            "best laptops 2024",
            "buy iphone online",
        ]
        results = await classifier.classify_batch(keywords)

        assert len(results) == 3
        for result in results:
            assert "keyword" in result
            assert "intent" in result
            assert "confidence" in result

    @pytest.mark.asyncio
    async def test_classify_empty_keyword(self, classifier):
        """Test classification of empty keyword."""
        result = await classifier.classify("")

        # Should return equal probabilities
        for intent in IntentClassifier.INTENT_CLASSES:
            assert result[intent] == 0.25

    @pytest.mark.asyncio
    async def test_classify_no_pattern_match(self, classifier):
        """Test classification when no patterns match."""
        result = await classifier.classify("random words here")

        # Should default to informational as primary
        assert result["informational"] > 0

    def test_get_intent_classifier_singleton(self):
        """Test that get_intent_classifier returns same instance."""
        classifier1 = get_intent_classifier(use_ml=False)
        classifier2 = get_intent_classifier(use_ml=False)

        assert classifier1 is classifier2


class TestIntentPatterns:
    """Tests for intent pattern matching."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return IntentClassifier(use_ml=False)

    @pytest.mark.asyncio
    async def test_how_to_pattern(self, classifier):
        """Test 'how to' pattern matches informational."""
        result = await classifier.get_primary_intent("how to fix a bike")
        assert result == "informational"

    @pytest.mark.asyncio
    async def test_what_is_pattern(self, classifier):
        """Test 'what is' pattern matches informational."""
        result = await classifier.get_primary_intent("what is blockchain")
        assert result == "informational"

    @pytest.mark.asyncio
    async def test_best_pattern(self, classifier):
        """Test 'best' pattern matches commercial."""
        result = await classifier.get_primary_intent("best coffee maker")
        assert result == "commercial"

    @pytest.mark.asyncio
    async def test_review_pattern(self, classifier):
        """Test 'review' pattern matches commercial."""
        result = await classifier.get_primary_intent("samsung galaxy review")
        assert result == "commercial"

    @pytest.mark.asyncio
    async def test_buy_pattern(self, classifier):
        """Test 'buy' pattern matches transactional."""
        result = await classifier.get_primary_intent("buy running shoes")
        assert result == "transactional"

    @pytest.mark.asyncio
    async def test_price_pattern(self, classifier):
        """Test 'price' pattern matches transactional."""
        result = await classifier.get_primary_intent("macbook price")
        assert result == "transactional"

    @pytest.mark.asyncio
    async def test_login_pattern(self, classifier):
        """Test 'login' pattern matches navigational."""
        result = await classifier.get_primary_intent("gmail login")
        assert result == "navigational"
