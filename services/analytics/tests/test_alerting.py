"""Tests for Alerting Engine."""

import pytest

from app.alerting import AlertingEngine, AlertLevel, AlertType, alerting_engine


class TestAlertingEngine:
    """Tests for Alerting Engine."""

    def test_init(self):
        """Test alerting engine initialization."""
        engine = AlertingEngine()
        assert engine._mock_mode is False
        assert len(engine._sent_alerts) == 0

    def test_enable_mock_mode(self):
        """Test enabling mock mode."""
        engine = AlertingEngine()
        engine.enable_mock_mode()
        assert engine._mock_mode is True

    def test_set_thresholds(self):
        """Test setting custom thresholds."""
        engine = AlertingEngine()
        engine.set_thresholds({"position_critical": 25.0})
        assert engine._thresholds["position_critical"] == 25.0

    @pytest.mark.asyncio
    async def test_check_cluster_performance_critical(self):
        """Test detecting critical cluster performance issues."""
        engine = AlertingEngine()
        engine.enable_mock_mode()

        performance_data = {
            "clusters": [
                {
                    "id": "cluster-123",
                    "name": "Poor Performing Cluster",
                    "avg_position": 25.0,
                    "total_clicks": 5,
                }
            ]
        }

        alerts = await engine.check_performance_issues("workspace-123", performance_data)

        # Should have at least one critical alert for position
        critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
        assert len(critical_alerts) >= 1
        assert critical_alerts[0].alert_type == AlertType.LOW_POSITION

    @pytest.mark.asyncio
    async def test_check_cluster_performance_warning(self):
        """Test detecting warning-level cluster performance issues."""
        engine = AlertingEngine()
        engine.enable_mock_mode()

        performance_data = {
            "clusters": [
                {
                    "id": "cluster-123",
                    "name": "Moderate Cluster",
                    "avg_position": 17.0,
                    "total_clicks": 50,
                }
            ]
        }

        alerts = await engine.check_performance_issues("workspace-123", performance_data)

        warning_alerts = [a for a in alerts if a.level == AlertLevel.WARNING]
        assert len(warning_alerts) >= 1

    @pytest.mark.asyncio
    async def test_check_low_clicks(self):
        """Test detecting low clicks alert."""
        engine = AlertingEngine()
        engine.enable_mock_mode()

        performance_data = {
            "clusters": [
                {
                    "id": "cluster-123",
                    "name": "Low Clicks Cluster",
                    "avg_position": 8.0,  # Good position
                    "total_clicks": 3,  # Low clicks
                }
            ]
        }

        alerts = await engine.check_performance_issues("workspace-123", performance_data)

        low_click_alerts = [a for a in alerts if a.alert_type == AlertType.LOW_CLICKS]
        assert len(low_click_alerts) == 1
        assert "3" in low_click_alerts[0].message

    @pytest.mark.asyncio
    async def test_check_declining_performance(self):
        """Test detecting declining rank alert."""
        engine = AlertingEngine()
        engine.enable_mock_mode()

        performance_data = {
            "declining": [
                {
                    "id": "article-123",
                    "name": "Declining Article",
                    "position_change": 8.0,
                    "current_position": 20.0,
                    "previous_position": 12.0,
                }
            ]
        }

        alerts = await engine.check_performance_issues("workspace-123", performance_data)

        declining_alerts = [
            a for a in alerts if a.alert_type == AlertType.DECLINING_RANK
        ]
        assert len(declining_alerts) == 1
        assert "8.0" in declining_alerts[0].message

    @pytest.mark.asyncio
    async def test_check_cost_efficiency(self):
        """Test detecting cost inefficiency alert."""
        engine = AlertingEngine()
        engine.enable_mock_mode()

        performance_data = {
            "cost_analysis": {
                "high_cost_low_performance": [
                    {
                        "title": "Expensive Poor Article",
                        "cost": 0.15,
                        "position": 45.0,
                    }
                ]
            }
        }

        alerts = await engine.check_performance_issues("workspace-123", performance_data)

        cost_alerts = [
            a for a in alerts if a.alert_type == AlertType.COST_INEFFICIENT
        ]
        assert len(cost_alerts) == 1
        assert "$0.15" in cost_alerts[0].message

    @pytest.mark.asyncio
    async def test_no_alerts_for_good_performance(self):
        """Test no alerts generated for good performance."""
        engine = AlertingEngine()
        engine.enable_mock_mode()

        performance_data = {
            "clusters": [
                {
                    "id": "cluster-123",
                    "name": "Good Cluster",
                    "avg_position": 5.0,
                    "total_clicks": 500,
                }
            ]
        }

        alerts = await engine.check_performance_issues("workspace-123", performance_data)

        assert len(alerts) == 0

    def test_get_sent_alerts(self):
        """Test retrieving sent alerts."""
        engine = AlertingEngine()
        engine.enable_mock_mode()
        assert engine.get_sent_alerts() == []

    def test_clear_alerts(self):
        """Test clearing alerts."""
        engine = AlertingEngine()
        engine.enable_mock_mode()
        engine._sent_alerts.append({})
        engine.clear_alerts()
        assert len(engine._sent_alerts) == 0

    @pytest.mark.asyncio
    async def test_check_cluster_alerts(self):
        """Test checking alerts for a specific cluster."""
        engine = AlertingEngine()
        engine.enable_mock_mode()

        cluster_data = {
            "name": "Test Cluster",
            "avg_position": 22.0,
            "total_clicks": 5,
        }

        alerts = await engine.check_cluster_alerts(
            "workspace-123", "cluster-123", cluster_data
        )

        assert len(alerts) > 0

    def test_global_instance(self):
        """Test global alerting engine instance exists."""
        assert alerting_engine is not None
        assert isinstance(alerting_engine, AlertingEngine)
