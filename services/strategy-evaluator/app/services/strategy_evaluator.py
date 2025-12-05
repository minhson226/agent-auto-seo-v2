"""Strategy Re-evaluation Engine for automatic strategy improvement."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ReEvaluationResult(BaseModel):
    """Result of a strategy re-evaluation."""

    cluster_id: str
    original_strategy: Dict[str, Any]
    new_strategy: Dict[str, Any]
    reason: str
    new_plan_id: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class ContentPlanRequest(BaseModel):
    """Request to create a new content plan."""

    cluster_id: str
    workspace_id: str
    title: str
    priority: str = "high"
    notes: Optional[str] = None
    ai_model: str = "gpt-4o"
    prompt_template: str = "detailed_v2"
    target_keywords: List[str] = []


class StrategyReEvaluator:
    """Engine for automatic strategy re-evaluation based on performance data."""

    # Minimum days before a cluster can be re-evaluated again
    MIN_DAYS_BETWEEN_EVALUATIONS = 7

    # Maximum re-evaluations per cluster per month
    MAX_EVALUATIONS_PER_MONTH = 4

    def __init__(self):
        """Initialize Strategy Re-evaluator."""
        self._mock_mode = False
        self._events_published: List[Dict[str, Any]] = []
        self._plans_created: List[ContentPlanRequest] = []
        self._cluster_cache: Dict[str, Dict[str, Any]] = {}
        self._thresholds = {
            "position_poor_threshold": 20.0,
            "min_days_for_evaluation": 30,
            "click_threshold": 10,
        }

    def enable_mock_mode(self):
        """Enable mock mode for testing."""
        self._mock_mode = True
        self._events_published = []
        self._plans_created = []

    def get_published_events(self) -> List[Dict[str, Any]]:
        """Get list of published events (for testing)."""
        return self._events_published

    def get_created_plans(self) -> List[ContentPlanRequest]:
        """Get list of created plans (for testing)."""
        return self._plans_created

    def set_thresholds(self, thresholds: Dict[str, Any]):
        """Update evaluation thresholds."""
        self._thresholds.update(thresholds)

    async def get_cluster(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cluster information by ID.

        Args:
            cluster_id: The cluster ID.

        Returns:
            Cluster data or None if not found.
        """
        if self._mock_mode and cluster_id in self._cluster_cache:
            return self._cluster_cache.get(cluster_id)

        # In real implementation, query the database
        logger.debug(f"Fetching cluster: {cluster_id}")
        return None

    def set_cluster_data(self, cluster_id: str, data: Dict[str, Any]):
        """Set cluster data for mock mode."""
        self._cluster_cache[cluster_id] = data

    async def get_cluster_performance(
        self, cluster_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get performance data for a cluster.

        Args:
            cluster_id: The cluster ID.
            days: Number of days to analyze.

        Returns:
            Performance metrics for the cluster.
        """
        if self._mock_mode and cluster_id in self._cluster_cache:
            cluster = self._cluster_cache.get(cluster_id, {})
            return cluster.get(
                "performance",
                {
                    "avg_position": 0.0,
                    "total_clicks": 0,
                    "total_impressions": 0,
                    "articles_count": 0,
                },
            )

        # In real implementation, query ClickHouse
        logger.debug(f"Fetching performance for cluster: {cluster_id}")
        return {
            "avg_position": 0.0,
            "total_clicks": 0,
            "total_impressions": 0,
            "articles_count": 0,
        }

    async def analyze_competitors(self, cluster: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze what's working for competitors in this topic area.

        Args:
            cluster: The cluster data.

        Returns:
            Competitor analysis with best practices.
        """
        # In real implementation, this would:
        # 1. Get keywords from the cluster
        # 2. Analyze top-ranking competitors
        # 3. Extract best practices

        return {
            "recommended_length": "long-form (2000+ words)",
            "recommended_structure": "comprehensive guides with sections",
            "recommended_model": "gpt-4o",
            "recommended_prompt": "detailed_v2",
            "competitor_insights": [
                "Top competitors use detailed, well-structured content",
                "Average word count of top 10 results: 2500 words",
                "Majority include tables, images, and code examples",
            ],
        }

    async def create_content_plan(
        self, plan_request: ContentPlanRequest
    ) -> Dict[str, Any]:
        """
        Create a new content plan based on re-evaluation.

        Args:
            plan_request: The content plan request.

        Returns:
            Created content plan data.
        """
        plan_id = str(uuid4())

        if self._mock_mode:
            self._plans_created.append(plan_request)
            return {
                "id": plan_id,
                "cluster_id": plan_request.cluster_id,
                "workspace_id": plan_request.workspace_id,
                "title": plan_request.title,
                "priority": plan_request.priority,
                "notes": plan_request.notes,
                "ai_model": plan_request.ai_model,
                "prompt_template": plan_request.prompt_template,
                "status": "draft",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        # In real implementation, call SEO Strategy service API
        logger.info(f"Creating content plan for cluster: {plan_request.cluster_id}")
        return {"id": plan_id}

    async def publish_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Publish event for other services to consume.

        Args:
            event_type: The event type.
            payload: The event payload.
        """
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }

        if self._mock_mode:
            self._events_published.append(event)
            logger.debug(f"Mock event published: {event_type}")
            return

        # In real implementation, publish to RabbitMQ
        logger.info(f"Publishing event: {event_type}")

    async def re_evaluate_cluster(self, cluster_id: str) -> ReEvaluationResult:
        """
        Re-evaluate a cluster's strategy based on performance.

        If the cluster has been underperforming for 30+ days,
        automatically create a new content plan with improved strategy.

        Args:
            cluster_id: The cluster ID to re-evaluate.

        Returns:
            Re-evaluation result with new plan if created.
        """
        cluster = await self.get_cluster(cluster_id)
        if not cluster:
            return ReEvaluationResult(
                cluster_id=cluster_id,
                original_strategy={},
                new_strategy={},
                reason="Cluster not found",
                success=False,
                error="Cluster not found",
            )

        performance = await self.get_cluster_performance(
            cluster_id, days=self._thresholds["min_days_for_evaluation"]
        )

        original_strategy = {
            "ai_model": cluster.get("ai_model", "gpt-3.5-turbo"),
            "prompt_template": cluster.get("prompt_template", "standard"),
        }

        # Check if performance is poor
        avg_position = performance.get("avg_position", 0.0)
        total_clicks = performance.get("total_clicks", 0)

        if avg_position > self._thresholds["position_poor_threshold"]:
            # Poor performance detected - create new strategy
            logger.info(
                f"Poor performance detected for cluster {cluster_id}: "
                f"avg_position={avg_position}"
            )

            # Analyze competitors for best practices
            best_practices = await self.analyze_competitors(cluster)

            # Determine new strategy
            new_strategy = {
                "ai_model": best_practices.get("recommended_model", "gpt-4o"),
                "prompt_template": best_practices.get(
                    "recommended_prompt", "detailed_v2"
                ),
            }

            # Create new content plan
            plan_request = ContentPlanRequest(
                cluster_id=cluster_id,
                workspace_id=cluster.get("workspace_id", ""),
                title=f"[Rewrite] {cluster.get('name', 'Unnamed Cluster')}",
                priority="high",
                notes=f"Re-evaluation due to poor performance (avg position: {avg_position:.1f}). "
                f"New strategy based on competitor analysis: {best_practices.get('competitor_insights', [])}",
                ai_model=new_strategy["ai_model"],
                prompt_template=new_strategy["prompt_template"],
                target_keywords=cluster.get("keywords", []),
            )

            new_plan = await self.create_content_plan(plan_request)

            # Publish event for content regeneration
            await self.publish_event(
                "content.plan.regenerate",
                {
                    "cluster_id": cluster_id,
                    "new_plan_id": new_plan.get("id"),
                    "reason": "poor_performance_30d",
                    "old_strategy": original_strategy,
                    "new_strategy": new_strategy,
                    "performance_metrics": performance,
                },
            )

            return ReEvaluationResult(
                cluster_id=cluster_id,
                original_strategy=original_strategy,
                new_strategy=new_strategy,
                reason=f"Poor performance: avg position {avg_position:.1f}, "
                f"{total_clicks} clicks in 30 days",
                new_plan_id=new_plan.get("id"),
                success=True,
            )

        # Performance is acceptable
        return ReEvaluationResult(
            cluster_id=cluster_id,
            original_strategy=original_strategy,
            new_strategy=original_strategy,  # Keep same strategy
            reason=f"Performance acceptable: avg position {avg_position:.1f}",
            success=True,
        )

    async def evaluate_workspace(self, workspace_id: str) -> List[ReEvaluationResult]:
        """
        Evaluate all clusters in a workspace and re-evaluate poor performers.

        Args:
            workspace_id: The workspace ID.

        Returns:
            List of re-evaluation results.
        """
        results = []

        # Get all clusters for workspace
        clusters = await self._get_workspace_clusters(workspace_id)

        for cluster in clusters:
            cluster_id = cluster.get("id")
            if cluster_id:
                result = await self.re_evaluate_cluster(cluster_id)
                results.append(result)

        # Log summary
        re_evaluated_count = sum(
            1 for r in results if r.new_plan_id is not None
        )
        logger.info(
            f"Workspace {workspace_id}: evaluated {len(results)} clusters, "
            f"re-evaluated {re_evaluated_count} poor performers"
        )

        return results

    async def _get_workspace_clusters(
        self, workspace_id: str
    ) -> List[Dict[str, Any]]:
        """Get all clusters for a workspace."""
        if self._mock_mode:
            return [
                {"id": cid, **data}
                for cid, data in self._cluster_cache.items()
                if data.get("workspace_id") == workspace_id
            ]

        # In real implementation, query the database
        logger.debug(f"Fetching clusters for workspace: {workspace_id}")
        return []


# Global strategy re-evaluator instance
strategy_evaluator = StrategyReEvaluator()


async def weekly_strategy_evaluation() -> Dict[str, Any]:
    """
    Weekly job to re-evaluate underperforming clusters across all workspaces.

    Returns:
        Summary of evaluation results.
    """
    logger.info("Starting weekly strategy evaluation")

    results = {
        "workspaces_processed": 0,
        "clusters_evaluated": 0,
        "plans_created": 0,
        "errors": [],
    }

    # In real implementation, get all active workspaces
    workspaces: List[Dict[str, Any]] = []  # await get_active_workspaces()

    for ws in workspaces:
        try:
            ws_results = await strategy_evaluator.evaluate_workspace(ws.get("id", ""))
            results["clusters_evaluated"] += len(ws_results)
            results["plans_created"] += sum(
                1 for r in ws_results if r.new_plan_id is not None
            )
            results["workspaces_processed"] += 1
        except Exception as e:
            error_msg = f"Failed to evaluate workspace {ws.get('id')}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)

    logger.info(
        f"Weekly strategy evaluation completed: "
        f"{results['workspaces_processed']} workspaces, "
        f"{results['clusters_evaluated']} clusters evaluated, "
        f"{results['plans_created']} new plans created"
    )

    return results
