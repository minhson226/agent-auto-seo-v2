"""Automated data sync tasks for GA4 and GSC."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.connectors.ga4_connector import GA4Connector
from app.connectors.gsc_connector import GSCConnector
from app.db.clickhouse import clickhouse_client

logger = logging.getLogger(__name__)


async def get_active_workspaces() -> List[Dict[str, Any]]:
    """
    Get list of active workspaces with analytics configured.

    Returns:
        List of workspace dictionaries with id and settings.
    """
    # In a real implementation, this would query the database
    # For now, return empty list as placeholder
    logger.debug("Fetching active workspaces with analytics configured")
    return []


async def get_sites(workspace_id: str) -> List[Dict[str, Any]]:
    """
    Get list of sites for a workspace.

    Args:
        workspace_id: The workspace ID.

    Returns:
        List of site dictionaries with url, ga_property_id, and gsc settings.
    """
    # In a real implementation, this would query the database
    logger.debug(f"Fetching sites for workspace: {workspace_id}")
    return []


async def insert_performance_data(
    ga_data: List[Dict[str, Any]],
    gsc_data: List[Dict[str, Any]],
    workspace_id: str,
    site_url: str,
) -> int:
    """
    Insert GA4 and GSC performance data into ClickHouse.

    Args:
        ga_data: List of GA4 page metrics.
        gsc_data: List of GSC performance data.
        workspace_id: The workspace ID.
        site_url: The site URL.

    Returns:
        Number of records inserted.
    """
    inserted_count = 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Create a map of GSC data by page path for joining
    gsc_by_page: Dict[str, Dict[str, Any]] = {}
    for gsc_row in gsc_data:
        page = gsc_row.get("page", "")
        if page:
            gsc_by_page[page] = gsc_row

    # Process GA4 data and merge with GSC data where available
    for ga_row in ga_data:
        page_path = ga_row.get("page_path", "")
        full_url = f"{site_url.rstrip('/')}{page_path}"

        # Get GSC metrics if available
        gsc_row = gsc_by_page.get(full_url, {})

        data = {
            "url": full_url,
            "date": today,
            "impressions": gsc_row.get("impressions", 0),
            "clicks": gsc_row.get("clicks", 0),
            "position": gsc_row.get("position", 0.0),
            "workspace_id": workspace_id,
            "article_id": "",  # Would need to match with articles table
            "ai_model_used": "",
            "prompt_id": "",
            "cost_usd": 0.0,
        }

        try:
            await clickhouse_client.insert_performance(data)
            inserted_count += 1
        except Exception as e:
            logger.error(f"Failed to insert performance data for {full_url}: {e}")

    # Also insert GSC data that wasn't in GA4
    for page_url, gsc_row in gsc_by_page.items():
        # Check if already processed from GA4
        ga_pages = [ga.get("page_path", "") for ga in ga_data]
        page_path = page_url.replace(site_url.rstrip("/"), "")
        if page_path not in ga_pages:
            data = {
                "url": page_url,
                "date": today,
                "impressions": gsc_row.get("impressions", 0),
                "clicks": gsc_row.get("clicks", 0),
                "position": gsc_row.get("position", 0.0),
                "workspace_id": workspace_id,
                "article_id": "",
                "ai_model_used": "",
                "prompt_id": "",
                "cost_usd": 0.0,
            }

            try:
                await clickhouse_client.insert_performance(data)
                inserted_count += 1
            except Exception as e:
                logger.error(f"Failed to insert GSC data for {page_url}: {e}")

    return inserted_count


async def update_article_performance_sync(workspace_id: str) -> int:
    """
    Update article performance summary in PostgreSQL.

    Args:
        workspace_id: The workspace ID.

    Returns:
        Number of articles updated.
    """
    # In a real implementation, this would update PostgreSQL
    # with aggregated performance data from ClickHouse
    logger.debug(f"Updating article performance for workspace: {workspace_id}")
    return 0


async def sync_analytics_daily(
    workspace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Daily job to sync GA4 and GSC data for all active workspaces.

    This task fetches data from Google Analytics 4 and Google Search Console,
    inserts it into ClickHouse for analysis, and updates PostgreSQL summaries.

    Args:
        workspace_id: Optional specific workspace to sync. If None, syncs all.

    Returns:
        Dictionary with sync results summary.
    """
    logger.info("Starting daily analytics sync")

    results = {
        "workspaces_processed": 0,
        "sites_synced": 0,
        "records_inserted": 0,
        "errors": [],
    }

    try:
        if workspace_id:
            workspaces = [{"id": workspace_id}]
        else:
            workspaces = await get_active_workspaces()

        for ws in workspaces:
            ws_id = ws.get("id", "")
            sites = await get_sites(ws_id)

            for site in sites:
                try:
                    site_url = site.get("url", "")
                    ga_property_id = site.get("ga_property_id")
                    gsc_credentials = site.get("gsc_credentials")
                    ga_credentials = site.get("ga_credentials")

                    # Calculate date range (yesterday's data) using UTC
                    now_utc = datetime.now(timezone.utc)
                    yesterday = (now_utc - timedelta(days=1)).strftime(
                        "%Y-%m-%d"
                    )
                    today = now_utc.strftime("%Y-%m-%d")

                    ga_data: List[Dict[str, Any]] = []
                    gsc_data: List[Dict[str, Any]] = []

                    # Sync GA4 data
                    if ga_property_id:
                        try:
                            ga4 = GA4Connector(
                                property_id=ga_property_id,
                                credentials_json=ga_credentials,
                            )
                            ga_data = await ga4.get_page_metrics(
                                start_date=yesterday, end_date=today
                            )
                            logger.info(
                                f"Fetched {len(ga_data)} GA4 records for {site_url}"
                            )
                        except Exception as e:
                            error_msg = f"GA4 sync failed for {site_url}: {str(e)}"
                            logger.error(error_msg)
                            results["errors"].append(error_msg)

                    # Sync GSC data
                    if site_url:
                        try:
                            gsc = GSCConnector(
                                site_url=site_url,
                                credentials_json=gsc_credentials,
                            )
                            gsc_data = await gsc.get_performance_data(
                                start_date=yesterday, end_date=today
                            )
                            logger.info(
                                f"Fetched {len(gsc_data)} GSC records for {site_url}"
                            )
                        except Exception as e:
                            error_msg = f"GSC sync failed for {site_url}: {str(e)}"
                            logger.error(error_msg)
                            results["errors"].append(error_msg)

                    # Insert into ClickHouse
                    if ga_data or gsc_data:
                        inserted = await insert_performance_data(
                            ga_data, gsc_data, ws_id, site_url
                        )
                        results["records_inserted"] += inserted

                    # Update PostgreSQL summary
                    await update_article_performance_sync(ws_id)

                    results["sites_synced"] += 1

                except Exception as e:
                    error_msg = f"Site sync failed for {site.get('url', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            results["workspaces_processed"] += 1

    except Exception as e:
        error_msg = f"Analytics sync failed: {str(e)}"
        logger.error(error_msg)
        results["errors"].append(error_msg)

    logger.info(
        f"Daily analytics sync completed: "
        f"{results['workspaces_processed']} workspaces, "
        f"{results['sites_synced']} sites, "
        f"{results['records_inserted']} records"
    )

    return results


async def sync_single_site(
    workspace_id: str,
    site_url: str,
    ga_property_id: Optional[str] = None,
    ga_credentials: Optional[Dict[str, Any]] = None,
    gsc_credentials: Optional[Dict[str, Any]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sync analytics for a single site.

    Args:
        workspace_id: The workspace ID.
        site_url: The site URL.
        ga_property_id: Optional GA4 property ID.
        ga_credentials: Optional GA4 credentials.
        gsc_credentials: Optional GSC credentials.
        start_date: Optional start date (defaults to yesterday).
        end_date: Optional end date (defaults to today).

    Returns:
        Dictionary with sync results.
    """
    now_utc = datetime.now(timezone.utc)
    if not start_date:
        start_date = (now_utc - timedelta(days=1)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = now_utc.strftime("%Y-%m-%d")

    results = {
        "ga4_records": 0,
        "gsc_records": 0,
        "inserted": 0,
        "success": True,
        "error": None,
    }

    try:
        ga_data: List[Dict[str, Any]] = []
        gsc_data: List[Dict[str, Any]] = []

        # Sync GA4
        if ga_property_id:
            ga4 = GA4Connector(
                property_id=ga_property_id, credentials_json=ga_credentials
            )
            ga_data = await ga4.get_page_metrics(
                start_date=start_date, end_date=end_date
            )
            results["ga4_records"] = len(ga_data)

        # Sync GSC
        gsc = GSCConnector(site_url=site_url, credentials_json=gsc_credentials)
        gsc_data = await gsc.get_performance_data(
            start_date=start_date, end_date=end_date
        )
        results["gsc_records"] = len(gsc_data)

        # Insert data
        if ga_data or gsc_data:
            results["inserted"] = await insert_performance_data(
                ga_data, gsc_data, workspace_id, site_url
            )

    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
        logger.error(f"Single site sync failed: {e}")

    return results
