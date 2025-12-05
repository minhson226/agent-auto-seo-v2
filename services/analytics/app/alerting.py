"""Alerting Engine for performance issue detection."""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of performance alerts."""

    LOW_POSITION = "low_position"
    LOW_CLICKS = "low_clicks"
    LOW_IMPRESSIONS = "low_impressions"
    DECLINING_RANK = "declining_rank"
    NO_DATA = "no_data"
    COST_INEFFICIENT = "cost_inefficient"


class Alert(BaseModel):
    """Performance alert model."""

    id: str
    workspace_id: str
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    data: Dict[str, Any]
    created_at: str
    acknowledged: bool = False

    @classmethod
    def create(
        cls,
        workspace_id: str,
        alert_type: AlertType,
        level: AlertLevel,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> "Alert":
        """Create a new alert."""
        return cls(
            id=str(uuid4()),
            workspace_id=workspace_id,
            alert_type=alert_type,
            level=level,
            title=title,
            message=message,
            data=data or {},
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class AlertingEngine:
    """Engine for detecting and sending performance alerts."""

    def __init__(self):
        """Initialize Alerting Engine."""
        self._mock_mode = False
        self._sent_alerts: List[Alert] = []
        self._thresholds = {
            "position_warning": 15.0,
            "position_critical": 20.0,
            "min_clicks_30d": 10,
            "min_impressions_30d": 100,
            "position_decline_threshold": 5.0,
        }

    def enable_mock_mode(self):
        """Enable mock mode for testing."""
        self._mock_mode = True
        self._sent_alerts = []

    def get_sent_alerts(self) -> List[Alert]:
        """Get list of sent alerts (for testing)."""
        return self._sent_alerts

    def clear_alerts(self):
        """Clear sent alerts (for testing)."""
        self._sent_alerts = []

    def set_thresholds(self, thresholds: Dict[str, Any]):
        """Update alert thresholds."""
        self._thresholds.update(thresholds)

    async def check_performance_issues(
        self, workspace_id: str, performance_data: Optional[Dict[str, Any]] = None
    ) -> List[Alert]:
        """
        Check for performance issues and generate alerts.

        Args:
            workspace_id: The workspace ID.
            performance_data: Optional performance data to check.

        Returns:
            List of generated alerts.
        """
        alerts = []

        # Check for clusters not performing well
        cluster_alerts = await self._check_cluster_performance(
            workspace_id, performance_data
        )
        alerts.extend(cluster_alerts)

        # Check for articles with declining ranks
        declining_alerts = await self._check_declining_performance(
            workspace_id, performance_data
        )
        alerts.extend(declining_alerts)

        # Check for cost inefficiency
        cost_alerts = await self._check_cost_efficiency(workspace_id, performance_data)
        alerts.extend(cost_alerts)

        # Send alerts
        for alert in alerts:
            await self._send_alert(alert)

        return alerts

    async def _check_cluster_performance(
        self, workspace_id: str, performance_data: Optional[Dict[str, Any]] = None
    ) -> List[Alert]:
        """Check for underperforming clusters."""
        alerts = []

        if performance_data and "clusters" in performance_data:
            for cluster in performance_data["clusters"]:
                cluster_name = cluster.get("name", "Unknown Cluster")
                avg_position = cluster.get("avg_position", 0.0)
                total_clicks = cluster.get("total_clicks", 0)

                # Critical: Very poor position
                if avg_position > self._thresholds["position_critical"]:
                    alert = Alert.create(
                        workspace_id=workspace_id,
                        alert_type=AlertType.LOW_POSITION,
                        level=AlertLevel.CRITICAL,
                        title=f"Critical: Poor ranking for '{cluster_name}'",
                        message=f"Cluster '{cluster_name}' has average position "
                        f"{avg_position:.1f} (below position 20). "
                        "Consider strategy re-evaluation.",
                        data={
                            "cluster_name": cluster_name,
                            "cluster_id": cluster.get("id"),
                            "avg_position": avg_position,
                            "total_clicks": total_clicks,
                        },
                    )
                    alerts.append(alert)
                # Warning: Moderate poor position
                elif avg_position > self._thresholds["position_warning"]:
                    alert = Alert.create(
                        workspace_id=workspace_id,
                        alert_type=AlertType.LOW_POSITION,
                        level=AlertLevel.WARNING,
                        title=f"Warning: Low ranking for '{cluster_name}'",
                        message=f"Cluster '{cluster_name}' has average position "
                        f"{avg_position:.1f}. Monitor closely.",
                        data={
                            "cluster_name": cluster_name,
                            "cluster_id": cluster.get("id"),
                            "avg_position": avg_position,
                            "total_clicks": total_clicks,
                        },
                    )
                    alerts.append(alert)

                # Check for low clicks
                if total_clicks < self._thresholds["min_clicks_30d"]:
                    alert = Alert.create(
                        workspace_id=workspace_id,
                        alert_type=AlertType.LOW_CLICKS,
                        level=AlertLevel.WARNING,
                        title=f"Low clicks for '{cluster_name}'",
                        message=f"Cluster '{cluster_name}' has only {total_clicks} "
                        "clicks in the last 30 days.",
                        data={
                            "cluster_name": cluster_name,
                            "cluster_id": cluster.get("id"),
                            "total_clicks": total_clicks,
                        },
                    )
                    alerts.append(alert)

        return alerts

    async def _check_declining_performance(
        self, workspace_id: str, performance_data: Optional[Dict[str, Any]] = None
    ) -> List[Alert]:
        """Check for articles or clusters with declining rankings."""
        alerts = []

        if performance_data and "declining" in performance_data:
            for item in performance_data["declining"]:
                name = item.get("name", "Unknown")
                position_change = item.get("position_change", 0.0)

                # Note: positive position_change means declining performance
                # (e.g., moving from position 5 to position 13 = position_change of 8)
                # Higher position numbers = worse rankings in search results
                if position_change > self._thresholds["position_decline_threshold"]:
                    alert = Alert.create(
                        workspace_id=workspace_id,
                        alert_type=AlertType.DECLINING_RANK,
                        level=AlertLevel.WARNING,
                        title=f"Declining rank for '{name}'",
                        message=f"'{name}' position has dropped by "
                        f"{position_change:.1f} in the last 7 days.",
                        data={
                            "name": name,
                            "id": item.get("id"),
                            "position_change": position_change,
                            "current_position": item.get("current_position"),
                            "previous_position": item.get("previous_position"),
                        },
                    )
                    alerts.append(alert)

        return alerts

    async def _check_cost_efficiency(
        self, workspace_id: str, performance_data: Optional[Dict[str, Any]] = None
    ) -> List[Alert]:
        """Check for cost inefficiency in content generation."""
        alerts = []

        if performance_data and "cost_analysis" in performance_data:
            cost_data = performance_data["cost_analysis"]
            high_cost_low_perf = cost_data.get("high_cost_low_performance", [])

            for item in high_cost_low_perf:
                alert = Alert.create(
                    workspace_id=workspace_id,
                    alert_type=AlertType.COST_INEFFICIENT,
                    level=AlertLevel.INFO,
                    title=f"High cost, low performance: {item.get('title', 'Unknown')}",
                    message=f"Content cost ${item.get('cost', 0):.2f} but "
                    f"position is {item.get('position', 0):.1f}. "
                    "Consider using more cost-effective models.",
                    data=item,
                )
                alerts.append(alert)

        return alerts

    async def _send_alert(self, alert: Alert):
        """Send an alert via configured channels."""
        self._sent_alerts.append(alert)

        if self._mock_mode:
            logger.debug(f"Mock alert sent: {alert.title}")
            return

        # In real implementation, this would:
        # 1. Store alert in database
        # 2. Send to notification service via RabbitMQ
        # 3. Trigger webhooks if configured
        logger.info(f"Alert sent: [{alert.level.value}] {alert.title}")

        # Publish event for notification service
        await self._publish_alert_event(alert)

    async def _publish_alert_event(self, alert: Alert):
        """Publish alert event for notification service to handle."""
        # In real implementation, publish to RabbitMQ
        event = {
            "event_type": "analytics.alert.created",
            "workspace_id": alert.workspace_id,
            "payload": {
                "alert_id": alert.id,
                "alert_type": alert.alert_type.value,
                "level": alert.level.value,
                "title": alert.title,
                "message": alert.message,
                "data": alert.data,
            },
        }
        logger.debug(f"Would publish event: {event['event_type']}")

    async def check_cluster_alerts(
        self, workspace_id: str, cluster_id: str, cluster_data: Dict[str, Any]
    ) -> List[Alert]:
        """
        Check alerts for a specific cluster.

        Args:
            workspace_id: The workspace ID.
            cluster_id: The cluster ID.
            cluster_data: Cluster performance data.

        Returns:
            List of alerts for this cluster.
        """
        performance_data = {"clusters": [{"id": cluster_id, **cluster_data}]}
        return await self.check_performance_issues(workspace_id, performance_data)


# Global alerting engine instance
alerting_engine = AlertingEngine()
