"""Tests for sync tasks."""

import pytest

from app.tasks.sync_tasks import (
    get_active_workspaces,
    get_sites,
    insert_performance_data,
    sync_analytics_daily,
    sync_single_site,
    update_article_performance_sync,
)


class TestSyncTasks:
    """Tests for analytics sync tasks."""

    @pytest.mark.asyncio
    async def test_get_active_workspaces(self):
        """Test getting active workspaces."""
        result = await get_active_workspaces()
        # Returns empty list as placeholder
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_sites(self):
        """Test getting sites for a workspace."""
        result = await get_sites("workspace-123")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_insert_performance_data_empty(self):
        """Test inserting empty performance data."""
        inserted = await insert_performance_data(
            ga_data=[],
            gsc_data=[],
            workspace_id="workspace-123",
            site_url="https://example.com",
        )
        assert inserted == 0

    @pytest.mark.asyncio
    async def test_insert_performance_data_with_ga_data(self, reset_clickhouse_mock):
        """Test inserting GA4 performance data."""
        ga_data = [
            {
                "page_path": "/article-1",
                "page_views": 100,
                "sessions": 50,
                "avg_session_duration": 120.0,
            }
        ]
        gsc_data = []

        inserted = await insert_performance_data(
            ga_data=ga_data,
            gsc_data=gsc_data,
            workspace_id="workspace-123",
            site_url="https://example.com",
        )

        assert inserted == 1

    @pytest.mark.asyncio
    async def test_insert_performance_data_with_gsc_data(self, reset_clickhouse_mock):
        """Test inserting GSC performance data."""
        ga_data = []
        gsc_data = [
            {
                "page": "https://example.com/article-1",
                "clicks": 50,
                "impressions": 500,
                "position": 8.5,
            }
        ]

        inserted = await insert_performance_data(
            ga_data=ga_data,
            gsc_data=gsc_data,
            workspace_id="workspace-123",
            site_url="https://example.com",
        )

        assert inserted == 1

    @pytest.mark.asyncio
    async def test_insert_performance_data_merged(self, reset_clickhouse_mock):
        """Test inserting merged GA4 and GSC data."""
        ga_data = [
            {
                "page_path": "/article-1",
                "page_views": 100,
                "sessions": 50,
                "avg_session_duration": 120.0,
            }
        ]
        gsc_data = [
            {
                "page": "https://example.com/article-1",
                "clicks": 50,
                "impressions": 500,
                "position": 8.5,
            }
        ]

        inserted = await insert_performance_data(
            ga_data=ga_data,
            gsc_data=gsc_data,
            workspace_id="workspace-123",
            site_url="https://example.com",
        )

        # Should insert GA data merged with GSC (matching page), plus standalone GSC
        # Since page_path "/article-1" doesn't match full URL "https://example.com/article-1"
        # both records should be inserted
        assert inserted >= 1

    @pytest.mark.asyncio
    async def test_update_article_performance_sync(self):
        """Test updating article performance sync."""
        updated = await update_article_performance_sync("workspace-123")
        # Returns 0 as placeholder
        assert updated == 0

    @pytest.mark.asyncio
    async def test_sync_analytics_daily_empty(self):
        """Test daily analytics sync with no workspaces."""
        results = await sync_analytics_daily()

        assert "workspaces_processed" in results
        assert "sites_synced" in results
        assert "records_inserted" in results
        assert "errors" in results

    @pytest.mark.asyncio
    async def test_sync_analytics_daily_specific_workspace(self):
        """Test daily analytics sync for specific workspace."""
        results = await sync_analytics_daily(workspace_id="workspace-123")

        assert results["workspaces_processed"] == 1
        assert isinstance(results["errors"], list)

    @pytest.mark.asyncio
    async def test_sync_single_site(self, reset_clickhouse_mock):
        """Test syncing a single site."""
        results = await sync_single_site(
            workspace_id="workspace-123",
            site_url="https://example.com",
        )

        assert "ga4_records" in results
        assert "gsc_records" in results
        assert "inserted" in results
        assert "success" in results

    @pytest.mark.asyncio
    async def test_sync_single_site_with_dates(self, reset_clickhouse_mock):
        """Test syncing a single site with custom dates."""
        results = await sync_single_site(
            workspace_id="workspace-123",
            site_url="https://example.com",
            start_date="2025-01-01",
            end_date="2025-01-31",
        )

        assert results["success"] is True
