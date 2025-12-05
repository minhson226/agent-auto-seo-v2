"""Tests for Performance Analyzer."""

import pytest

from app.analyzer import PerformanceAnalyzer, performance_analyzer


class TestPerformanceAnalyzer:
    """Tests for Performance Analyzer."""

    def test_init(self):
        """Test analyzer initialization."""
        analyzer = PerformanceAnalyzer()
        assert analyzer._mock_mode is False

    def test_enable_mock_mode(self):
        """Test enabling mock mode."""
        analyzer = PerformanceAnalyzer()
        mock_data = {
            "model_performance": [
                {"ai_model_used": "gpt-4o", "avg_position": 8.5, "avg_cost": 0.05}
            ]
        }
        analyzer.enable_mock_mode(mock_data)
        assert analyzer._mock_mode is True
        assert analyzer._mock_data == mock_data

    @pytest.mark.asyncio
    async def test_analyze_model_performance_mock(self):
        """Test model performance analysis in mock mode."""
        analyzer = PerformanceAnalyzer()
        mock_data = {
            "model_performance": [
                {
                    "ai_model_used": "gpt-4o",
                    "article_count": 10,
                    "avg_position": 8.5,
                    "total_clicks": 500,
                    "avg_cost": 0.05,
                },
                {
                    "ai_model_used": "gpt-3.5-turbo",
                    "article_count": 20,
                    "avg_position": 12.3,
                    "total_clicks": 300,
                    "avg_cost": 0.01,
                },
            ]
        }
        analyzer.enable_mock_mode(mock_data)

        result = await analyzer.analyze_model_performance("workspace-123", days=30)

        assert len(result) == 2
        assert result[0]["ai_model_used"] == "gpt-4o"
        assert result[0]["avg_position"] == 8.5

    @pytest.mark.asyncio
    async def test_analyze_cost_vs_rank_mock(self):
        """Test cost vs rank analysis in mock mode."""
        analyzer = PerformanceAnalyzer()
        mock_data = {
            "cost_vs_rank": {
                "correlation": -0.65,
                "avg_cost_top_10": 0.08,
                "avg_cost_10_20": 0.04,
                "avg_cost_below_20": 0.02,
                "recommendation": "Higher cost models correlate with better rankings",
            }
        }
        analyzer.enable_mock_mode(mock_data)

        result = await analyzer.analyze_cost_vs_rank("workspace-123", days=30)

        assert result["correlation"] == -0.65
        assert result["avg_cost_top_10"] == 0.08
        assert "recommendation" in result

    @pytest.mark.asyncio
    async def test_get_cluster_performance_mock(self):
        """Test cluster performance retrieval in mock mode."""
        analyzer = PerformanceAnalyzer()
        mock_data = {
            "cluster_performance": {
                "cluster_id": "cluster-123",
                "avg_position": 15.0,
                "total_clicks": 50,
                "total_impressions": 500,
                "articles_ranking": 5,
            }
        }
        analyzer.enable_mock_mode(mock_data)

        result = await analyzer.get_cluster_performance("cluster-123", days=30)

        assert result["cluster_id"] == "cluster-123"
        assert result["avg_position"] == 15.0

    @pytest.mark.asyncio
    async def test_get_underperforming_clusters_mock(self):
        """Test underperforming clusters retrieval in mock mode."""
        analyzer = PerformanceAnalyzer()
        mock_data = {
            "underperforming_clusters": [
                {
                    "cluster_id": "cluster-1",
                    "name": "SEO Tips",
                    "avg_position": 25.0,
                    "total_clicks": 5,
                },
                {
                    "cluster_id": "cluster-2",
                    "name": "Marketing Guide",
                    "avg_position": 22.0,
                    "total_clicks": 8,
                },
            ]
        }
        analyzer.enable_mock_mode(mock_data)

        result = await analyzer.get_underperforming_clusters("workspace-123")

        assert len(result) == 2
        assert result[0]["avg_position"] == 25.0

    @pytest.mark.asyncio
    async def test_get_trending_topics_mock(self):
        """Test trending topics retrieval in mock mode."""
        analyzer = PerformanceAnalyzer()
        mock_data = {
            "trending_topics": [
                {
                    "topic": "AI Content",
                    "position_improvement": 5.0,
                    "clicks_increase": 100,
                }
            ]
        }
        analyzer.enable_mock_mode(mock_data)

        result = await analyzer.get_trending_topics("workspace-123")

        assert len(result) == 1
        assert result[0]["position_improvement"] == 5.0

    @pytest.mark.asyncio
    async def test_generate_insights_report(self):
        """Test insights report generation."""
        analyzer = PerformanceAnalyzer()
        analyzer.enable_mock_mode({})

        result = await analyzer.generate_insights_report("workspace-123", days=30)

        assert result["workspace_id"] == "workspace-123"
        assert result["period_days"] == 30
        assert "model_performance" in result
        assert "recommendations" in result

    def test_global_instance(self):
        """Test global analyzer instance exists."""
        assert performance_analyzer is not None
        assert isinstance(performance_analyzer, PerformanceAnalyzer)
