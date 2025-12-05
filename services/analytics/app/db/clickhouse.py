"""ClickHouse database client."""

import hashlib
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ClickHouseClient:
    """ClickHouse database client for analytics data."""

    def __init__(self):
        """Initialize ClickHouse client."""
        self._client = None
        self._connected = False
        self._mock_mode = False
        self._mock_data: List[Dict[str, Any]] = []

    async def connect(self) -> None:
        """Connect to ClickHouse database."""
        try:
            # Check if we should use mock mode
            if settings.CLICKHOUSE_HOST.startswith("mock://"):
                logger.info("Using mock ClickHouse client")
                self._mock_mode = True
                self._connected = True
                return

            import clickhouse_connect

            self._client = clickhouse_connect.get_client(
                host=settings.CLICKHOUSE_HOST,
                port=settings.CLICKHOUSE_PORT,
                username=settings.CLICKHOUSE_USER,
                password=settings.CLICKHOUSE_PASSWORD,
                database=settings.CLICKHOUSE_DATABASE,
            )
            self._connected = True
            logger.info("Connected to ClickHouse")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            # Fall back to mock mode if connection fails
            self._mock_mode = True
            self._connected = True
            logger.info("Falling back to mock ClickHouse client")

    async def disconnect(self) -> None:
        """Disconnect from ClickHouse database."""
        if self._client:
            self._client.close()
            self._client = None
        self._connected = False
        logger.info("Disconnected from ClickHouse")

    async def is_connected(self) -> bool:
        """Check if connected to ClickHouse."""
        if self._mock_mode:
            return True
        if self._client:
            try:
                self._client.ping()
                return True
            except Exception:
                return False
        return False

    @staticmethod
    def url_hash(url: str) -> str:
        """Generate SHA-256 hash of URL for secure identification."""
        return hashlib.sha256(url.encode()).hexdigest()

    async def insert_performance(self, data: Dict[str, Any]) -> bool:
        """Insert performance data into fact_performance table."""
        if self._mock_mode:
            self._mock_data.append(data)
            logger.debug(f"Mock insert: {data}")
            return True

        if not self._client:
            raise RuntimeError("ClickHouse client not connected")

        try:
            # Prepare data for insertion
            row = [
                data["date"],
                self.url_hash(data["url"]),
                data["url"],
                data.get("workspace_id", ""),
                data.get("article_id", ""),
                data.get("impressions", 0),
                data.get("clicks", 0),
                data.get("position", 0.0),
                data.get("ai_model_used", ""),
                data.get("prompt_id", ""),
                data.get("cost_usd", 0.0),
            ]

            self._client.insert(
                "fact_performance",
                [row],
                column_names=[
                    "date",
                    "url_hash",
                    "url",
                    "workspace_id",
                    "article_id",
                    "impressions",
                    "clicks",
                    "position",
                    "ai_model_used",
                    "prompt_id",
                    "cost_usd",
                ],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to insert performance data: {e}")
            raise

    async def get_summary(
        self, workspace_id: str, date_from: str, date_to: str
    ) -> Dict[str, Any]:
        """Get performance summary for a workspace."""
        if self._mock_mode:
            # Filter mock data by workspace_id and date range
            filtered_data = [
                d
                for d in self._mock_data
                if d.get("workspace_id") == workspace_id
                and date_from <= str(d.get("date", "")) <= date_to
            ]

            if not filtered_data:
                return {
                    "total_impressions": 0,
                    "total_clicks": 0,
                    "avg_position": 0.0,
                    "articles_ranking": 0,
                    "top_articles": [],
                }

            total_impressions = sum(d.get("impressions", 0) for d in filtered_data)
            total_clicks = sum(d.get("clicks", 0) for d in filtered_data)
            positions = [d.get("position", 0.0) for d in filtered_data if d.get("position", 0.0) > 0]
            avg_position = sum(positions) / len(positions) if positions else 0.0
            unique_articles = set(d.get("article_id", "") for d in filtered_data if d.get("article_id"))

            return {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "avg_position": round(avg_position, 2),
                "articles_ranking": len(unique_articles),
                "top_articles": [],
            }

        if not self._client:
            raise RuntimeError("ClickHouse client not connected")

        try:
            query = """
            SELECT
                sum(impressions) as total_impressions,
                sum(clicks) as total_clicks,
                avg(position) as avg_position,
                count(DISTINCT article_id) as articles_ranking
            FROM fact_performance
            WHERE workspace_id = %(workspace_id)s
              AND date BETWEEN %(date_from)s AND %(date_to)s
            """

            result = self._client.query(
                query,
                parameters={
                    "workspace_id": workspace_id,
                    "date_from": date_from,
                    "date_to": date_to,
                },
            )

            if result.result_rows:
                row = result.result_rows[0]
                return {
                    "total_impressions": int(row[0] or 0),
                    "total_clicks": int(row[1] or 0),
                    "avg_position": round(float(row[2] or 0), 2),
                    "articles_ranking": int(row[3] or 0),
                    "top_articles": await self._get_top_articles(workspace_id, date_from, date_to),
                }
            return {
                "total_impressions": 0,
                "total_clicks": 0,
                "avg_position": 0.0,
                "articles_ranking": 0,
                "top_articles": [],
            }
        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            raise

    async def _get_top_articles(
        self, workspace_id: str, date_from: str, date_to: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top performing articles."""
        if not self._client:
            return []

        try:
            query = """
            SELECT
                article_id,
                url,
                sum(impressions) as total_impressions,
                sum(clicks) as total_clicks,
                avg(position) as avg_position
            FROM fact_performance
            WHERE workspace_id = %(workspace_id)s
              AND date BETWEEN %(date_from)s AND %(date_to)s
              AND article_id != ''
            GROUP BY article_id, url
            ORDER BY total_clicks DESC
            LIMIT %(limit)s
            """

            result = self._client.query(
                query,
                parameters={
                    "workspace_id": workspace_id,
                    "date_from": date_from,
                    "date_to": date_to,
                    "limit": limit,
                },
            )

            return [
                {
                    "article_id": row[0],
                    "url": row[1],
                    "total_impressions": int(row[2]),
                    "total_clicks": int(row[3]),
                    "avg_position": round(float(row[4]), 2),
                }
                for row in result.result_rows
            ]
        except Exception as e:
            logger.error(f"Failed to get top articles: {e}")
            return []

    async def get_article_performance(
        self, article_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get time series performance data for a specific article."""
        if self._mock_mode:
            # Filter mock data by article_id
            filtered_data = [
                d for d in self._mock_data if d.get("article_id") == article_id
            ]
            return [
                {
                    "date": str(d.get("date", "")),
                    "impressions": d.get("impressions", 0),
                    "clicks": d.get("clicks", 0),
                    "position": d.get("position", 0.0),
                }
                for d in filtered_data
            ]

        if not self._client:
            raise RuntimeError("ClickHouse client not connected")

        try:
            query = """
            SELECT
                date,
                sum(impressions) as impressions,
                sum(clicks) as clicks,
                avg(position) as position
            FROM fact_performance
            WHERE article_id = %(article_id)s
              AND date >= today() - %(days)s
            GROUP BY date
            ORDER BY date
            """

            result = self._client.query(
                query,
                parameters={
                    "article_id": article_id,
                    "days": days,
                },
            )

            return [
                {
                    "date": str(row[0]),
                    "impressions": int(row[1]),
                    "clicks": int(row[2]),
                    "position": round(float(row[3]), 2),
                }
                for row in result.result_rows
            ]
        except Exception as e:
            logger.error(f"Failed to get article performance: {e}")
            raise

    def clear_mock_data(self) -> None:
        """Clear mock data (for testing)."""
        self._mock_data = []


# Global client instance
clickhouse_client = ClickHouseClient()
