"""Tests for Auto Scoring components (PHASE-010).

This module tests the HTMLAnalyzer, AutoScorer, TacticalCorrector,
and AdaptiveScorer classes.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.html_analyzer import HTMLAnalyzer
from app.services.auto_scorer import AutoScorer
from app.services.corrector import TacticalCorrector
from app.services.adaptive_scorer import AdaptiveScorer


class TestHTMLAnalyzer:
    """Tests for HTMLAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return HTMLAnalyzer()

    @pytest.fixture
    def sample_html(self):
        """Sample HTML for testing."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Best SEO Tips for Marketing Success</title>
            <meta name="description" content="Learn the best SEO tips for marketing success in 2024">
        </head>
        <body>
            <h1>Best SEO Tips</h1>
            <p>Welcome to our comprehensive guide on SEO tips.</p>
            <h2>Understanding SEO</h2>
            <p>SEO is the process of optimizing your website for search engines.
               Marketing success depends on good SEO practices.</p>
            <h2>Top Marketing Strategies</h2>
            <p>Here are some marketing strategies to boost your traffic.</p>
            <img src="image1.jpg" alt="SEO diagram">
            <img src="image2.jpg" alt="Marketing chart">
            <a href="/internal-page">Learn more</a>
            <a href="https://example.com">External resource</a>
        </body>
        </html>
        """

    def test_analyze_returns_expected_keys(self, analyzer, sample_html):
        """Test that analyze returns all expected keys."""
        result = analyzer.analyze(sample_html, ["seo", "marketing"])

        expected_keys = [
            "title_contains_keyword",
            "h1_present",
            "h1_count",
            "h1_contains_keyword",
            "h2_count",
            "h2_contains_keyword",
            "keyword_density",
            "keyword_density_ok",
            "images_count",
            "images_with_alt",
            "images_without_alt",
            "images_have_alt",
            "word_count",
            "word_count_adequate",
            "internal_links",
            "external_links",
            "has_internal_links",
            "has_external_links",
            "meta_description",
            "meta_description_length",
            "title_length",
            "score",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_analyze_detects_keyword_in_title(self, analyzer, sample_html):
        """Test keyword detection in title."""
        result = analyzer.analyze(sample_html, ["seo"])
        assert result["title_contains_keyword"] is True

        result = analyzer.analyze(sample_html, ["python"])
        assert result["title_contains_keyword"] is False

    def test_analyze_detects_h1(self, analyzer, sample_html):
        """Test H1 detection."""
        result = analyzer.analyze(sample_html, ["seo"])
        assert result["h1_present"] is True
        assert result["h1_count"] == 1
        assert result["h1_contains_keyword"] is True

    def test_analyze_counts_h2(self, analyzer, sample_html):
        """Test H2 counting."""
        result = analyzer.analyze(sample_html, ["seo"])
        assert result["h2_count"] == 2

    def test_analyze_detects_images_with_alt(self, analyzer, sample_html):
        """Test image alt tag detection."""
        result = analyzer.analyze(sample_html, ["seo"])
        assert result["images_count"] == 2
        assert result["images_with_alt"] == 2
        assert result["images_without_alt"] == 0
        assert result["images_have_alt"] is True

    def test_analyze_detects_images_without_alt(self, analyzer):
        """Test detection of images missing alt tags."""
        html = '<html><body><img src="test.jpg"></body></html>'
        result = analyzer.analyze(html, ["test"])
        assert result["images_count"] == 1
        assert result["images_with_alt"] == 0
        assert result["images_without_alt"] == 1
        assert result["images_have_alt"] is False

    def test_analyze_counts_links(self, analyzer, sample_html):
        """Test link counting."""
        result = analyzer.analyze(sample_html, ["seo"])
        assert result["internal_links"] == 1
        assert result["external_links"] == 1
        assert result["has_internal_links"] is True
        assert result["has_external_links"] is True

    def test_analyze_detects_meta_description(self, analyzer, sample_html):
        """Test meta description detection."""
        result = analyzer.analyze(sample_html, ["seo"])
        assert result["meta_description"] is True
        assert result["meta_description_length"] > 0

    def test_analyze_empty_html(self, analyzer):
        """Test analysis of empty HTML."""
        result = analyzer.analyze("", ["seo"])
        assert result["h1_present"] is False
        assert result["word_count"] == 0

    def test_keyword_density_calculation(self, analyzer):
        """Test keyword density calculation."""
        html = """
        <html><body>
        SEO SEO SEO SEO SEO other words here for testing
        more words SEO SEO SEO SEO SEO to pad the count
        </body></html>
        """
        result = analyzer.analyze(html, ["seo"])
        assert result["keyword_density"] > 0


class TestAutoScorer:
    """Tests for AutoScorer."""

    @pytest.fixture
    def scorer(self):
        """Create scorer instance."""
        return AutoScorer()

    @pytest.fixture
    def perfect_analysis(self):
        """Analysis with all items passing."""
        return {
            "title_contains_keyword": True,
            "h1_present": True,
            "h1_contains_keyword": True,
            "h2_contains_keyword": True,
            "keyword_density_ok": True,
            "images_have_alt": True,
            "word_count_adequate": True,
            "has_internal_links": True,
            "has_external_links": True,
            "meta_description": True,
        }

    @pytest.fixture
    def partial_analysis(self):
        """Analysis with some items passing."""
        return {
            "title_contains_keyword": True,
            "h1_present": True,
            "h1_contains_keyword": True,
            "h2_contains_keyword": False,
            "keyword_density_ok": True,
            "images_have_alt": True,
            "word_count_adequate": False,
            "has_internal_links": True,
            "has_external_links": False,
            "meta_description": True,
        }

    def test_score_perfect_analysis(self, scorer, perfect_analysis):
        """Test scoring a perfect analysis."""
        score = scorer.score(perfect_analysis)
        assert score == 100

    def test_score_partial_analysis(self, scorer, partial_analysis):
        """Test scoring a partial analysis."""
        score = scorer.score(partial_analysis)
        assert 50 <= score < 100

    def test_score_empty_analysis(self, scorer):
        """Test scoring empty analysis."""
        score = scorer.score({})
        assert score == 0

    def test_get_detailed_score(self, scorer, perfect_analysis):
        """Test detailed scoring."""
        detailed = scorer.get_detailed_score(perfect_analysis)

        assert "score" in detailed
        assert "breakdown" in detailed
        assert "status" in detailed
        assert detailed["score"] == 100
        assert detailed["status"] == "approved"

    def test_status_approved(self, scorer):
        """Test approved status for high scores."""
        analysis = {
            "title_contains_keyword": True,
            "h1_present": True,
            "h1_contains_keyword": True,
            "h2_contains_keyword": True,
            "keyword_density_ok": True,
            "images_have_alt": True,
            "word_count_adequate": True,
            "has_internal_links": True,
            "has_external_links": True,
            "meta_description": True,
        }
        detailed = scorer.get_detailed_score(analysis)
        assert detailed["status"] == "approved"

    def test_status_needs_correction(self, scorer):
        """Test needs_correction status for low scores."""
        analysis = {
            "title_contains_keyword": False,
            "h1_present": False,
            "h1_contains_keyword": False,
            "h2_contains_keyword": False,
            "keyword_density_ok": False,
            "images_have_alt": False,
            "word_count_adequate": False,
            "has_internal_links": False,
            "has_external_links": False,
            "meta_description": False,
        }
        detailed = scorer.get_detailed_score(analysis)
        assert detailed["status"] == "needs_correction"

    def test_identify_issues(self, scorer, partial_analysis):
        """Test issue identification."""
        issues = scorer.identify_issues(partial_analysis)

        assert "missing_keyword_in_h2" in issues
        assert "low_word_count" in issues
        assert "no_external_links" in issues

    def test_get_correction_suggestions(self, scorer):
        """Test getting correction suggestions."""
        issues = ["missing_keyword_in_title", "low_word_count"]
        suggestions = scorer.get_correction_suggestions(issues)

        assert len(suggestions) == 2
        assert any("title" in s["suggestion"].lower() for s in suggestions)
        assert any("word" in s["suggestion"].lower() for s in suggestions)

    def test_custom_weights(self):
        """Test scoring with custom weights."""
        custom_weights = {
            "title_contains_keyword": 50,
            "h1_present": 50,
        }
        scorer = AutoScorer(weights=custom_weights)

        analysis = {"title_contains_keyword": True, "h1_present": False}
        score = scorer.score(analysis)
        assert score == 50


class TestTacticalCorrector:
    """Tests for TacticalCorrector."""

    @pytest.fixture
    def corrector(self):
        """Create corrector instance."""
        return TacticalCorrector()

    @pytest.mark.asyncio
    async def test_correct_approves_high_score(self, corrector):
        """Test that high scores are approved."""
        score_data = {"score": 85}

        with patch.object(corrector, "_publish_approved_event", new_callable=AsyncMock):
            result = await corrector.correct("article-123", score_data)

        assert result["action"] == "approved"
        assert result["score"] == 85

    @pytest.mark.asyncio
    async def test_correct_requests_correction_for_low_score(self, corrector):
        """Test that low scores trigger correction request."""
        score_data = {
            "score": 60,
            "breakdown": {
                "title_contains_keyword": {"passed": False},
                "h1_present": {"passed": True},
            },
        }

        with patch.object(
            corrector, "_publish_regeneration_event", new_callable=AsyncMock
        ):
            result = await corrector.correct("article-123", score_data)

        assert result["action"] == "correction_requested"
        assert result["correction_attempt"] == 1
        assert len(result["issues"]) > 0

    @pytest.mark.asyncio
    async def test_correct_respects_max_attempts(self, corrector):
        """Test that max correction attempts are respected."""
        score_data = {"score": 60}

        result = await corrector.correct(
            "article-123", score_data, correction_attempt=3
        )

        assert result["action"] == "manual_review_required"
        assert result["correction_attempt"] == 3

    @pytest.mark.asyncio
    async def test_evaluate_and_correct(self, corrector):
        """Test the combined evaluate and correct method."""
        html = """
        <html>
        <head><title>SEO Guide</title></head>
        <body>
            <h1>SEO Guide</h1>
            <p>Content about SEO</p>
        </body>
        </html>
        """

        with patch.object(
            corrector, "_publish_regeneration_event", new_callable=AsyncMock
        ):
            result = await corrector.evaluate_and_correct(
                "article-123", html, ["seo"]
            )

        assert "action" in result
        assert "score" in result


class TestAdaptiveScorer:
    """Tests for AdaptiveScorer."""

    @pytest.fixture
    def adaptive_scorer(self):
        """Create adaptive scorer instance."""
        return AdaptiveScorer()

    @pytest.fixture
    def training_data(self):
        """Sample training data."""
        return [
            {
                "seo_checklist_values": {
                    "title_contains_keyword": True,
                    "h1_present": True,
                    "h1_contains_keyword": True,
                    "h2_contains_keyword": True,
                    "keyword_density_ok": True,
                    "images_have_alt": True,
                    "word_count_adequate": True,
                    "has_internal_links": True,
                    "has_external_links": True,
                    "meta_description": True,
                },
                "avg_position": 5,  # Good ranking
            },
            {
                "seo_checklist_values": {
                    "title_contains_keyword": False,
                    "h1_present": True,
                    "h1_contains_keyword": False,
                    "h2_contains_keyword": False,
                    "keyword_density_ok": False,
                    "images_have_alt": True,
                    "word_count_adequate": False,
                    "has_internal_links": False,
                    "has_external_links": False,
                    "meta_description": False,
                },
                "avg_position": 50,  # Poor ranking
            },
        ] * 6  # Repeat to get enough samples

    def test_train_insufficient_data(self, adaptive_scorer):
        """Test training with insufficient data."""
        result = adaptive_scorer.train([{"seo_checklist_values": {}, "avg_position": 5}])
        assert result["success"] is False
        assert result["reason"] == "insufficient_data"

    def test_train_with_sufficient_data(self, adaptive_scorer, training_data):
        """Test training with sufficient data."""
        result = adaptive_scorer.train(training_data)

        assert result["success"] is True
        assert "learned_weights" in result
        assert "model_accuracy" in result

    def test_train_returns_weights(self, adaptive_scorer, training_data):
        """Test that training returns valid weights."""
        result = adaptive_scorer.train(training_data)

        if result["success"]:
            weights = result["learned_weights"]
            assert isinstance(weights, dict)
            for value in weights.values():
                assert isinstance(value, int)
                assert value >= 1

    def test_get_scorer_with_learned_weights(self, adaptive_scorer, training_data):
        """Test getting scorer with learned weights."""
        adaptive_scorer.train(training_data)
        scorer = adaptive_scorer.get_scorer_with_learned_weights()

        assert isinstance(scorer, AutoScorer)

    def test_predict_ranking_probability_before_training(self, adaptive_scorer):
        """Test prediction before training returns None."""
        result = adaptive_scorer.predict_ranking_probability({})
        assert result is None

    def test_predict_ranking_probability_after_training(
        self, adaptive_scorer, training_data
    ):
        """Test prediction after training returns probability."""
        adaptive_scorer.train(training_data)

        checklist = {
            "title_contains_keyword": True,
            "h1_present": True,
            "h1_contains_keyword": True,
            "h2_contains_keyword": True,
            "keyword_density_ok": True,
            "images_have_alt": True,
            "word_count_adequate": True,
            "has_internal_links": True,
            "has_external_links": True,
            "meta_description": True,
        }

        probability = adaptive_scorer.predict_ranking_probability(checklist)

        if probability is not None:
            assert 0 <= probability <= 1


class TestAutoScoringAPI:
    """Tests for Auto Scoring API endpoints."""

    @pytest.fixture
    def sample_html(self):
        """Sample HTML for testing."""
        return """
        <html>
        <head>
            <title>SEO Best Practices</title>
            <meta name="description" content="Learn SEO best practices">
        </head>
        <body>
            <h1>SEO Best Practices</h1>
            <h2>Introduction to SEO</h2>
            <p>SEO is important for online visibility.</p>
            <img src="test.jpg" alt="SEO illustration">
            <a href="/about">About us</a>
            <a href="https://example.com">External link</a>
        </body>
        </html>
        """

    @pytest.mark.asyncio
    async def test_auto_score_endpoint(
        self, async_client, auth_headers, sample_html
    ):
        """Test the auto score endpoint."""
        response = await async_client.post(
            "/api/v1/auto-score",
            json={
                "html_content": sample_html,
                "target_keywords": ["seo"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "status" in data
        assert "analysis" in data
        assert "detailed_score" in data

    @pytest.mark.asyncio
    async def test_analyze_endpoint(
        self, async_client, auth_headers, sample_html
    ):
        """Test the analyze endpoint."""
        response = await async_client.post(
            "/api/v1/auto-score/analyze",
            json={
                "html_content": sample_html,
                "target_keywords": ["seo"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "title_contains_keyword" in data
        assert "h1_present" in data
        assert "h2_count" in data

    @pytest.mark.asyncio
    async def test_get_weights_endpoint(self, async_client, auth_headers):
        """Test the get weights endpoint."""
        response = await async_client.get(
            "/api/v1/auto-score/weights",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "weights" in data
        assert "threshold_approved" in data

    @pytest.mark.asyncio
    async def test_correct_endpoint(
        self, async_client, auth_headers, sample_html
    ):
        """Test the correction endpoint."""
        response = await async_client.post(
            "/api/v1/auto-score/correct",
            json={
                "article_id": "test-article-123",
                "html_content": sample_html,
                "target_keywords": ["seo"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "action" in data
        assert "article_id" in data
        assert "score" in data

    @pytest.mark.asyncio
    async def test_auto_score_unauthorized(self, async_client, sample_html):
        """Test auto score without authentication."""
        response = await async_client.post(
            "/api/v1/auto-score",
            json={
                "html_content": sample_html,
                "target_keywords": ["seo"],
            },
        )

        assert response.status_code in [401, 403]
