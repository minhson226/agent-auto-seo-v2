"""Tests for ML automation features - clustering, prediction, and content plan generation."""

import pytest
import numpy as np
from uuid import uuid4

from app.ml.clustering import KeywordClusterer, get_keyword_clusterer
from app.ml.predictor import RankingPredictor, get_ranking_predictor
from app.ml.content_plan_generator import ContentPlanGenerator, get_content_plan_generator


class TestKeywordClusterer:
    """Tests for KeywordClusterer."""

    def test_init_clusterer(self):
        """Test clusterer initialization."""
        clusterer = KeywordClusterer(use_semantic=False)
        assert clusterer is not None
        assert clusterer.use_semantic is False

    def test_cluster_tfidf_basic(self):
        """Test basic TF-IDF clustering."""
        clusterer = KeywordClusterer(use_semantic=False)
        keywords = [
            "python programming tutorial",
            "learn python basics",
            "python for beginners",
            "javascript web development",
            "react frontend framework",
            "nodejs backend",
        ]

        result = clusterer.cluster_tfidf(keywords, n_clusters=2)

        assert "labels" in result
        assert "clusters" in result
        assert len(result["labels"]) == len(keywords)
        assert len(result["clusters"]) == 2

    def test_cluster_tfidf_empty(self):
        """Test clustering with empty list."""
        clusterer = KeywordClusterer(use_semantic=False)
        result = clusterer.cluster_tfidf([], n_clusters=2)

        assert result["labels"] == []
        assert result["clusters"] == {}

    def test_cluster_tfidf_single_keyword(self):
        """Test clustering with single keyword."""
        clusterer = KeywordClusterer(use_semantic=False)
        result = clusterer.cluster_tfidf(["single keyword"], n_clusters=2)

        assert result["labels"] == [0]
        assert 0 in result["clusters"]

    def test_cluster_tfidf_adjusts_n_clusters(self):
        """Test that n_clusters is adjusted when fewer keywords."""
        clusterer = KeywordClusterer(use_semantic=False)
        keywords = ["keyword1", "keyword2", "keyword3"]

        # Request more clusters than keywords
        result = clusterer.cluster_tfidf(keywords, n_clusters=10)

        # Should create 3 clusters (one per keyword max)
        assert len(result["clusters"]) <= 3

    def test_cluster_semantic_fallback(self):
        """Test semantic clustering falls back to TF-IDF when SBERT unavailable."""
        clusterer = KeywordClusterer(use_semantic=False)  # Disable semantic
        keywords = [
            "machine learning",
            "deep learning",
            "artificial intelligence",
        ]

        result = clusterer.cluster_semantic(keywords)

        # Should still return valid clusters (via fallback)
        assert "labels" in result
        assert "clusters" in result

    def test_get_keyword_clusterer_singleton(self):
        """Test singleton pattern for clusterer."""
        clusterer1 = get_keyword_clusterer(use_semantic=False)
        clusterer2 = get_keyword_clusterer(use_semantic=False)

        # Should return the same instance
        assert clusterer1 is clusterer2


class TestRankingPredictor:
    """Tests for RankingPredictor."""

    def test_init_predictor(self):
        """Test predictor initialization."""
        predictor = RankingPredictor()
        assert predictor is not None
        assert predictor._is_trained is False

    def test_heuristic_predict(self):
        """Test heuristic prediction when model not trained."""
        predictor = RankingPredictor()

        features = np.array([
            [30, 1000, 0.3, 2000, 50, 10, 80, 1500, 40]  # Easy keyword, good metrics
        ])

        probabilities = predictor.predict_ranking_probability(features)

        assert len(probabilities) == 1
        assert 0 <= probabilities[0] <= 1

    def test_predict_from_dict(self):
        """Test prediction from dictionary input."""
        predictor = RankingPredictor()

        data = {
            "keyword_difficulty": 30,
            "search_volume": 1000,
            "competition": 0.3,
            "content_word_count": 2000,
            "domain_authority": 50,
            "backlink_count": 10,
            "content_quality_score": 80,
            "avg_competitor_word_count": 1500,
            "avg_competitor_da": 40,
        }

        result = predictor.predict_from_dict(data)

        assert "probability" in result
        assert "prediction" in result
        assert "will_rank" in result
        assert "confidence" in result
        assert 0 <= result["probability"] <= 1

    def test_create_features_from_dict(self):
        """Test feature array creation from dictionary."""
        predictor = RankingPredictor()

        data = {
            "keyword_difficulty": 50,
            "search_volume": 500,
        }

        features = predictor.create_features_from_dict(data)

        assert len(features) == len(predictor.FEATURE_NAMES)
        assert features[0] == 50  # keyword_difficulty
        assert features[1] == 500  # search_volume

    def test_predict_binary(self):
        """Test binary prediction."""
        predictor = RankingPredictor()

        features = np.array([
            [30, 1000, 0.3, 2000, 50, 10, 80, 1500, 40],
            [90, 100, 0.9, 500, 10, 0, 30, 3000, 80],
        ])

        predictions = predictor.predict(features, threshold=0.5)

        assert len(predictions) == 2
        assert all(p in [0, 1] for p in predictions)

    def test_get_ranking_predictor_singleton(self):
        """Test singleton pattern for predictor."""
        predictor1 = get_ranking_predictor()
        predictor2 = get_ranking_predictor()

        assert predictor1 is predictor2


class TestContentPlanGenerator:
    """Tests for ContentPlanGenerator."""

    def test_init_generator(self):
        """Test generator initialization."""
        generator = ContentPlanGenerator()
        assert generator is not None

    def test_determine_priority_high(self):
        """Test high priority determination."""
        generator = ContentPlanGenerator()

        priority = generator.determine_priority(
            keyword_difficulty=30,
            search_volume=2000,
            competition=0.3,
        )

        assert priority == "high"

    def test_determine_priority_medium(self):
        """Test medium priority determination."""
        generator = ContentPlanGenerator()

        priority = generator.determine_priority(
            keyword_difficulty=50,
            search_volume=800,
            competition=0.5,
        )

        assert priority == "medium"

    def test_determine_priority_low(self):
        """Test low priority determination."""
        generator = ContentPlanGenerator()

        priority = generator.determine_priority(
            keyword_difficulty=80,
            search_volume=200,
            competition=0.9,
        )

        assert priority == "low"

    def test_suggest_content_type_how_to(self):
        """Test content type suggestion for how-to content."""
        generator = ContentPlanGenerator()

        content_type = generator.suggest_content_type(
            keywords=["how to learn python", "python tutorial", "step by step"],
            primary_keyword="how to learn python",
        )

        assert content_type == "how_to_guide"

    def test_suggest_content_type_listicle(self):
        """Test content type suggestion for listicle."""
        generator = ContentPlanGenerator()

        content_type = generator.suggest_content_type(
            keywords=["best python frameworks", "top libraries"],
            primary_keyword="best python frameworks",
        )

        assert content_type == "listicle"

    def test_suggest_content_type_comparison(self):
        """Test content type suggestion for comparison."""
        generator = ContentPlanGenerator()

        content_type = generator.suggest_content_type(
            keywords=["python vs javascript", "comparison"],
            primary_keyword="python vs javascript",
        )

        assert content_type == "comparison"

    def test_estimate_word_count(self):
        """Test word count estimation."""
        generator = ContentPlanGenerator()

        # Without competitor data
        word_count = generator.estimate_word_count("blog_post")
        assert word_count == 2000  # Default average

        # With competitor data
        word_count_with_comp = generator.estimate_word_count(
            "blog_post", competitor_avg_word_count=1500
        )
        assert word_count_with_comp == 1800  # 20% more than competitor

    def test_generate_title_suggestions(self):
        """Test title suggestion generation."""
        generator = ContentPlanGenerator()

        titles = generator.generate_title_suggestions(
            primary_keyword="python programming",
            content_type="how_to_guide",
            count=3,
        )

        assert len(titles) == 3
        assert all("python" in t.lower() for t in titles)

    def test_generate_outline(self):
        """Test outline generation."""
        generator = ContentPlanGenerator()

        outline = generator.generate_outline(
            primary_keyword="python programming",
            related_keywords=["python basics", "python syntax", "python functions"],
            content_type="how_to_guide",
        )

        assert len(outline) > 0
        assert all("heading" in section for section in outline)
        assert any("step" in section["heading"].lower() for section in outline)

    def test_generate_content_plan_complete(self):
        """Test complete content plan generation."""
        generator = ContentPlanGenerator()

        plan = generator.generate_content_plan(
            cluster_id=uuid4(),
            workspace_id=uuid4(),
            keywords=["python programming", "learn python", "python basics"],
            primary_keyword="python programming",
            keyword_metrics={"difficulty": 40, "volume": 1500, "competition": 0.4},
            competitor_data={"avg_word_count": 2000},
        )

        assert "id" in plan
        assert "title" in plan
        assert "priority" in plan
        assert "estimated_word_count" in plan
        assert "outline" in plan
        assert "seo_recommendations" in plan
        assert plan["status"] == "draft"

    def test_generate_batch_content_plans(self):
        """Test batch content plan generation."""
        generator = ContentPlanGenerator()

        clusters = [
            {
                "id": str(uuid4()),
                "keywords": ["python", "python programming"],
                "primary_keyword": "python programming",
                "metrics": {"difficulty": 40, "volume": 1000},
            },
            {
                "id": str(uuid4()),
                "keywords": ["javascript", "js"],
                "primary_keyword": "javascript",
                "metrics": {"difficulty": 35, "volume": 1200},
            },
        ]

        plans = generator.generate_batch_content_plans(clusters, uuid4())

        assert len(plans) == 2
        assert all("title" in p for p in plans)

    def test_get_content_plan_generator_singleton(self):
        """Test singleton pattern for generator."""
        generator1 = get_content_plan_generator()
        generator2 = get_content_plan_generator()

        assert generator1 is generator2


class TestMLIntegration:
    """Integration tests for ML features working together."""

    def test_cluster_then_generate_plans(self):
        """Test clustering keywords and then generating plans for each cluster."""
        # Cluster keywords
        clusterer = KeywordClusterer(use_semantic=False)
        keywords = [
            "how to learn python",
            "python tutorial for beginners",
            "python programming guide",
            "javascript framework",
            "react js tutorial",
            "nodejs backend",
        ]

        cluster_result = clusterer.cluster_tfidf(keywords, n_clusters=2)

        # Generate plans for each cluster
        generator = ContentPlanGenerator()
        workspace_id = uuid4()

        plans = []
        for cluster_id, cluster_keywords in cluster_result["clusters"].items():
            if cluster_keywords:
                plan = generator.generate_content_plan(
                    cluster_id=uuid4(),
                    workspace_id=workspace_id,
                    keywords=cluster_keywords,
                    primary_keyword=cluster_keywords[0],
                )
                plans.append(plan)

        assert len(plans) == 2
        assert all("title" in p for p in plans)

    def test_predict_then_prioritize(self):
        """Test using predictions to prioritize content plans."""
        predictor = RankingPredictor()
        generator = ContentPlanGenerator()

        # Test data for multiple keywords
        keyword_data = [
            {"keyword_difficulty": 30, "search_volume": 2000, "keyword": "easy keyword"},
            {"keyword_difficulty": 70, "search_volume": 500, "keyword": "hard keyword"},
        ]

        results = []
        for data in keyword_data:
            prediction = predictor.predict_from_dict(data)
            priority = generator.determine_priority(
                keyword_difficulty=data["keyword_difficulty"],
                search_volume=data["search_volume"],
            )
            results.append({
                "keyword": data["keyword"],
                "ranking_probability": prediction["probability"],
                "priority": priority,
            })

        # Easy keyword should have higher probability
        assert results[0]["ranking_probability"] > results[1]["ranking_probability"]
        # Easy keyword should have higher priority
        assert results[0]["priority"] in ["high", "medium"]
