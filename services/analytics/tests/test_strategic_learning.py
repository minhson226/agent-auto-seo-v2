"""Tests for Strategic Learning API endpoints."""

import pytest


class TestSyncEndpoints:
    """Tests for analytics sync endpoints."""

    def test_trigger_sync(self, client):
        """Test triggering analytics sync."""
        response = client.post(
            "/api/v1/strategic-learning/sync",
            json={},
        )
        assert response.status_code == 200
        result = response.json()
        assert "success" in result
        assert "workspaces_processed" in result

    def test_trigger_sync_specific_workspace(self, client):
        """Test triggering sync for specific workspace."""
        response = client.post(
            "/api/v1/strategic-learning/sync",
            json={"workspace_id": "test-workspace-123"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["workspaces_processed"] == 1

    def test_sync_single_site_missing_params(self, client):
        """Test single site sync with missing parameters."""
        response = client.post(
            "/api/v1/strategic-learning/sync/site",
            json={},
        )
        assert response.status_code == 400

    def test_sync_single_site(self, client):
        """Test single site sync."""
        response = client.post(
            "/api/v1/strategic-learning/sync/site",
            json={
                "workspace_id": "test-workspace-123",
                "site_url": "https://example.com",
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert "success" in result
        assert "ga4_records" in result
        assert "gsc_records" in result


class TestAnalysisEndpoints:
    """Tests for analysis endpoints."""

    def test_get_model_performance(self, client):
        """Test getting model performance analysis."""
        response = client.get(
            "/api/v1/strategic-learning/analysis/models",
            params={"workspace_id": "test-workspace-123"},
        )
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_get_model_performance_custom_days(self, client):
        """Test getting model performance with custom days."""
        response = client.get(
            "/api/v1/strategic-learning/analysis/models",
            params={"workspace_id": "test-workspace-123", "days": 60},
        )
        assert response.status_code == 200

    def test_get_model_performance_missing_workspace(self, client):
        """Test getting model performance without workspace_id."""
        response = client.get("/api/v1/strategic-learning/analysis/models")
        assert response.status_code == 422

    def test_get_cost_analysis(self, client):
        """Test getting cost vs rank analysis."""
        response = client.get(
            "/api/v1/strategic-learning/analysis/cost",
            params={"workspace_id": "test-workspace-123"},
        )
        assert response.status_code == 200
        result = response.json()
        assert "correlation" in result
        assert "recommendation" in result

    def test_get_insights_report(self, client):
        """Test getting comprehensive insights report."""
        response = client.get(
            "/api/v1/strategic-learning/analysis/insights",
            params={"workspace_id": "test-workspace-123"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["workspace_id"] == "test-workspace-123"
        assert "model_performance" in result
        assert "recommendations" in result

    def test_get_cluster_performance(self, client):
        """Test getting cluster performance."""
        response = client.get(
            "/api/v1/strategic-learning/analysis/clusters/cluster-123",
            params={"days": 30},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["cluster_id"] == "cluster-123"

    def test_get_underperforming_clusters(self, client):
        """Test getting underperforming clusters."""
        response = client.get(
            "/api/v1/strategic-learning/analysis/underperforming",
            params={"workspace_id": "test-workspace-123"},
        )
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_get_underperforming_clusters_custom_threshold(self, client):
        """Test getting underperforming clusters with custom threshold."""
        response = client.get(
            "/api/v1/strategic-learning/analysis/underperforming",
            params={
                "workspace_id": "test-workspace-123",
                "position_threshold": 15.0,
            },
        )
        assert response.status_code == 200


class TestAlertEndpoints:
    """Tests for alert endpoints."""

    def test_check_alerts_empty(self, client):
        """Test checking alerts with no data."""
        response = client.post(
            "/api/v1/strategic-learning/alerts/check",
            params={"workspace_id": "test-workspace-123"},
            json={},
        )
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_check_alerts_with_poor_cluster(self, client):
        """Test checking alerts with poor performing cluster."""
        response = client.post(
            "/api/v1/strategic-learning/alerts/check",
            params={"workspace_id": "test-workspace-123"},
            json={
                "clusters": [
                    {
                        "id": "cluster-123",
                        "name": "Poor Cluster",
                        "avg_position": 25.0,
                        "total_clicks": 5,
                    }
                ]
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result) > 0
        # Should have critical alert for position > 20
        critical_alerts = [a for a in result if a["level"] == "critical"]
        assert len(critical_alerts) >= 1

    def test_check_alerts_with_declining_content(self, client):
        """Test checking alerts with declining content."""
        response = client.post(
            "/api/v1/strategic-learning/alerts/check",
            params={"workspace_id": "test-workspace-123"},
            json={
                "declining": [
                    {
                        "id": "article-123",
                        "name": "Declining Article",
                        "position_change": 8.0,
                    }
                ]
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result) > 0
        # Should have warning alert for declining rank
        declining_alerts = [a for a in result if a["alert_type"] == "declining_rank"]
        assert len(declining_alerts) >= 1

    def test_alert_response_format(self, client):
        """Test alert response has correct format."""
        response = client.post(
            "/api/v1/strategic-learning/alerts/check",
            params={"workspace_id": "test-workspace-123"},
            json={
                "clusters": [
                    {
                        "id": "cluster-123",
                        "name": "Test Cluster",
                        "avg_position": 25.0,
                        "total_clicks": 3,
                    }
                ]
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result) > 0

        alert = result[0]
        assert "id" in alert
        assert "workspace_id" in alert
        assert "alert_type" in alert
        assert "level" in alert
        assert "title" in alert
        assert "message" in alert
        assert "created_at" in alert
