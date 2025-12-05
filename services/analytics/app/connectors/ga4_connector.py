"""Google Analytics 4 Connector for data integration."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GA4Connector:
    """Connector for Google Analytics 4 API integration."""

    def __init__(
        self,
        property_id: str,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize GA4 Connector.

        Args:
            property_id: The GA4 property ID.
            credentials_path: Path to service account credentials JSON file.
            credentials_json: Service account credentials as dictionary.
        """
        self.property_id = property_id
        self.credentials_path = credentials_path
        self.credentials_json = credentials_json
        self._client = None
        self._mock_mode = False
        self._mock_data: List[Dict[str, Any]] = []

    def _get_client(self):
        """Get or create the GA4 API client."""
        if self._mock_mode:
            return None

        if self._client is None:
            try:
                from google.analytics.data_v1beta import BetaAnalyticsDataClient
                from google.oauth2 import service_account

                if self.credentials_path:
                    credentials = service_account.Credentials.from_service_account_file(
                        self.credentials_path
                    )
                    self._client = BetaAnalyticsDataClient(credentials=credentials)
                elif self.credentials_json:
                    credentials = service_account.Credentials.from_service_account_info(
                        self.credentials_json
                    )
                    self._client = BetaAnalyticsDataClient(credentials=credentials)
                else:
                    # Use default credentials (e.g., from environment)
                    self._client = BetaAnalyticsDataClient()
            except ImportError:
                logger.warning(
                    "google-analytics-data package not installed, using mock mode"
                )
                self._mock_mode = True
            except Exception as e:
                logger.error(f"Failed to initialize GA4 client: {e}")
                self._mock_mode = True

        return self._client

    def enable_mock_mode(self, mock_data: Optional[List[Dict[str, Any]]] = None):
        """Enable mock mode for testing."""
        self._mock_mode = True
        self._mock_data = mock_data or []

    async def get_page_metrics(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Get page-level metrics from GA4.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            List of page metrics with pagePath, screenPageViews, sessions,
            and averageSessionDuration.
        """
        if self._mock_mode:
            logger.debug("Using mock GA4 data")
            return self._mock_data

        client = self._get_client()
        if client is None:
            return []

        try:
            from google.analytics.data_v1beta.types import RunReportRequest

            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[{"name": "pagePath"}],
                metrics=[
                    {"name": "screenPageViews"},
                    {"name": "sessions"},
                    {"name": "averageSessionDuration"},
                ],
                date_ranges=[{"start_date": start_date, "end_date": end_date}],
            )

            response = client.run_report(request)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Failed to fetch GA4 metrics: {e}")
            raise

    def _parse_response(self, response) -> List[Dict[str, Any]]:
        """Parse GA4 API response into list of dictionaries."""
        results = []
        for row in response.rows:
            result = {
                "page_path": row.dimension_values[0].value,
                "page_views": int(row.metric_values[0].value),
                "sessions": int(row.metric_values[1].value),
                "avg_session_duration": float(row.metric_values[2].value),
            }
            results.append(result)
        return results

    async def get_traffic_sources(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Get traffic source metrics from GA4.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            List of traffic source metrics.
        """
        if self._mock_mode:
            return []

        client = self._get_client()
        if client is None:
            return []

        try:
            from google.analytics.data_v1beta.types import RunReportRequest

            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[
                    {"name": "sessionSource"},
                    {"name": "sessionMedium"},
                ],
                metrics=[
                    {"name": "sessions"},
                    {"name": "activeUsers"},
                    {"name": "bounceRate"},
                ],
                date_ranges=[{"start_date": start_date, "end_date": end_date}],
            )

            response = client.run_report(request)
            results = []
            for row in response.rows:
                result = {
                    "source": row.dimension_values[0].value,
                    "medium": row.dimension_values[1].value,
                    "sessions": int(row.metric_values[0].value),
                    "users": int(row.metric_values[1].value),
                    "bounce_rate": float(row.metric_values[2].value),
                }
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"Failed to fetch GA4 traffic sources: {e}")
            raise

    async def get_engagement_metrics(
        self, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Get overall engagement metrics from GA4.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            Dictionary with overall engagement metrics.
        """
        if self._mock_mode:
            return {
                "total_users": 0,
                "new_users": 0,
                "engaged_sessions": 0,
                "engagement_rate": 0.0,
                "avg_engagement_time": 0.0,
            }

        client = self._get_client()
        if client is None:
            return {}

        try:
            from google.analytics.data_v1beta.types import RunReportRequest

            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                metrics=[
                    {"name": "totalUsers"},
                    {"name": "newUsers"},
                    {"name": "engagedSessions"},
                    {"name": "engagementRate"},
                    {"name": "averageSessionDuration"},
                ],
                date_ranges=[{"start_date": start_date, "end_date": end_date}],
            )

            response = client.run_report(request)
            if response.rows:
                row = response.rows[0]
                return {
                    "total_users": int(row.metric_values[0].value),
                    "new_users": int(row.metric_values[1].value),
                    "engaged_sessions": int(row.metric_values[2].value),
                    "engagement_rate": float(row.metric_values[3].value),
                    "avg_engagement_time": float(row.metric_values[4].value),
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch GA4 engagement metrics: {e}")
            raise
