"""Tests for Strategy Re-evaluator."""

import pytest

from app.services.strategy_evaluator import (
    ContentPlanRequest,
    ReEvaluationResult,
    StrategyReEvaluator,
    strategy_evaluator,
    weekly_strategy_evaluation,
)


class TestStrategyReEvaluator:
    """Tests for Strategy Re-evaluator."""

    def test_init(self):
        """Test strategy re-evaluator initialization."""
        evaluator = StrategyReEvaluator()
        assert evaluator._mock_mode is False

    def test_enable_mock_mode(self):
        """Test enabling mock mode."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()
        assert evaluator._mock_mode is True
        assert evaluator._events_published == []
        assert evaluator._plans_created == []

    def test_set_thresholds(self):
        """Test setting custom thresholds."""
        evaluator = StrategyReEvaluator()
        evaluator.set_thresholds({"position_poor_threshold": 25.0})
        assert evaluator._thresholds["position_poor_threshold"] == 25.0

    def test_set_cluster_data(self):
        """Test setting cluster data for mock mode."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()
        evaluator.set_cluster_data(
            "cluster-123",
            {"name": "Test Cluster", "workspace_id": "workspace-123"},
        )
        assert "cluster-123" in evaluator._cluster_cache

    @pytest.mark.asyncio
    async def test_get_cluster_mock(self):
        """Test getting cluster in mock mode."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()
        evaluator.set_cluster_data(
            "cluster-123",
            {"name": "Test Cluster", "workspace_id": "workspace-123"},
        )

        result = await evaluator.get_cluster("cluster-123")

        assert result is not None
        assert result["name"] == "Test Cluster"

    @pytest.mark.asyncio
    async def test_get_cluster_not_found(self):
        """Test getting non-existent cluster."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()

        result = await evaluator.get_cluster("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_cluster_performance_mock(self):
        """Test getting cluster performance in mock mode."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()
        evaluator.set_cluster_data(
            "cluster-123",
            {
                "name": "Test Cluster",
                "performance": {
                    "avg_position": 15.0,
                    "total_clicks": 50,
                    "total_impressions": 500,
                    "articles_count": 5,
                },
            },
        )

        result = await evaluator.get_cluster_performance("cluster-123", days=30)

        assert result["avg_position"] == 15.0
        assert result["total_clicks"] == 50

    @pytest.mark.asyncio
    async def test_analyze_competitors(self):
        """Test competitor analysis."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()

        cluster = {"name": "Test Cluster", "keywords": ["seo", "marketing"]}
        result = await evaluator.analyze_competitors(cluster)

        assert "recommended_model" in result
        assert "recommended_prompt" in result
        assert "competitor_insights" in result

    @pytest.mark.asyncio
    async def test_create_content_plan_mock(self):
        """Test creating content plan in mock mode."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()

        plan_request = ContentPlanRequest(
            cluster_id="cluster-123",
            workspace_id="workspace-123",
            title="[Rewrite] Test Cluster",
            priority="high",
            ai_model="gpt-4o",
            prompt_template="detailed_v2",
        )

        result = await evaluator.create_content_plan(plan_request)

        assert result["id"] is not None
        assert result["cluster_id"] == "cluster-123"
        assert result["title"] == "[Rewrite] Test Cluster"
        assert len(evaluator.get_created_plans()) == 1

    @pytest.mark.asyncio
    async def test_publish_event_mock(self):
        """Test publishing event in mock mode."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()

        await evaluator.publish_event(
            "content.plan.regenerate",
            {"cluster_id": "cluster-123", "reason": "test"},
        )

        events = evaluator.get_published_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "content.plan.regenerate"

    @pytest.mark.asyncio
    async def test_re_evaluate_cluster_not_found(self):
        """Test re-evaluating non-existent cluster."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()

        result = await evaluator.re_evaluate_cluster("non-existent")

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_re_evaluate_cluster_good_performance(self):
        """Test re-evaluating cluster with good performance."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()
        evaluator.set_cluster_data(
            "cluster-123",
            {
                "name": "Good Cluster",
                "workspace_id": "workspace-123",
                "ai_model": "gpt-3.5-turbo",
                "prompt_template": "standard",
                "performance": {
                    "avg_position": 8.0,  # Good position
                    "total_clicks": 100,
                    "total_impressions": 1000,
                },
            },
        )

        result = await evaluator.re_evaluate_cluster("cluster-123")

        assert result.success is True
        assert result.new_plan_id is None  # No new plan needed
        assert "acceptable" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_re_evaluate_cluster_poor_performance(self):
        """Test re-evaluating cluster with poor performance."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()
        evaluator.set_cluster_data(
            "cluster-123",
            {
                "name": "Poor Cluster",
                "workspace_id": "workspace-123",
                "ai_model": "gpt-3.5-turbo",
                "prompt_template": "standard",
                "keywords": ["seo", "tips"],
                "performance": {
                    "avg_position": 25.0,  # Poor position
                    "total_clicks": 5,
                    "total_impressions": 100,
                },
            },
        )

        result = await evaluator.re_evaluate_cluster("cluster-123")

        assert result.success is True
        assert result.new_plan_id is not None  # New plan created
        assert result.new_strategy["ai_model"] == "gpt-4o"
        assert "poor" in result.reason.lower()

        # Check event was published
        events = evaluator.get_published_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "content.plan.regenerate"
        assert events[0]["payload"]["reason"] == "poor_performance_30d"

    @pytest.mark.asyncio
    async def test_evaluate_workspace(self):
        """Test evaluating all clusters in a workspace."""
        evaluator = StrategyReEvaluator()
        evaluator.enable_mock_mode()

        # Add clusters to workspace
        evaluator.set_cluster_data(
            "cluster-1",
            {
                "name": "Good Cluster",
                "workspace_id": "workspace-123",
                "performance": {"avg_position": 5.0, "total_clicks": 200},
            },
        )
        evaluator.set_cluster_data(
            "cluster-2",
            {
                "name": "Poor Cluster",
                "workspace_id": "workspace-123",
                "performance": {"avg_position": 25.0, "total_clicks": 5},
            },
        )

        results = await evaluator.evaluate_workspace("workspace-123")

        assert len(results) == 2
        # One should be re-evaluated (poor), one should not (good)
        re_evaluated = [r for r in results if r.new_plan_id is not None]
        assert len(re_evaluated) == 1

    @pytest.mark.asyncio
    async def test_weekly_strategy_evaluation(self):
        """Test weekly strategy evaluation job."""
        result = await weekly_strategy_evaluation()

        assert "workspaces_processed" in result
        assert "clusters_evaluated" in result
        assert "plans_created" in result
        assert "errors" in result

    def test_global_instance(self):
        """Test global strategy evaluator instance exists."""
        assert strategy_evaluator is not None
        assert isinstance(strategy_evaluator, StrategyReEvaluator)


class TestContentPlanRequest:
    """Tests for ContentPlanRequest model."""

    def test_default_values(self):
        """Test default values for content plan request."""
        request = ContentPlanRequest(
            cluster_id="cluster-123",
            workspace_id="workspace-123",
            title="Test Plan",
        )

        assert request.priority == "high"
        assert request.ai_model == "gpt-4o"
        assert request.prompt_template == "detailed_v2"
        assert request.target_keywords == []

    def test_custom_values(self):
        """Test custom values for content plan request."""
        request = ContentPlanRequest(
            cluster_id="cluster-123",
            workspace_id="workspace-123",
            title="Test Plan",
            priority="medium",
            ai_model="gpt-3.5-turbo",
            prompt_template="standard",
            target_keywords=["seo", "marketing"],
        )

        assert request.priority == "medium"
        assert request.ai_model == "gpt-3.5-turbo"
        assert len(request.target_keywords) == 2


class TestReEvaluationResult:
    """Tests for ReEvaluationResult model."""

    def test_success_result(self):
        """Test successful re-evaluation result."""
        result = ReEvaluationResult(
            cluster_id="cluster-123",
            original_strategy={"ai_model": "gpt-3.5-turbo"},
            new_strategy={"ai_model": "gpt-4o"},
            reason="Poor performance",
            new_plan_id="plan-456",
            success=True,
        )

        assert result.success is True
        assert result.new_plan_id == "plan-456"
        assert result.error is None

    def test_failed_result(self):
        """Test failed re-evaluation result."""
        result = ReEvaluationResult(
            cluster_id="cluster-123",
            original_strategy={},
            new_strategy={},
            reason="Cluster not found",
            success=False,
            error="Cluster not found",
        )

        assert result.success is False
        assert result.error == "Cluster not found"
        assert result.new_plan_id is None
