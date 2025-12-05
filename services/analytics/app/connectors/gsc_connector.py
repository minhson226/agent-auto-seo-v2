"""Google Search Console Connector for data integration."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GSCConnector:
    """Connector for Google Search Console API integration."""

    def __init__(
        self,
        site_url: str,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize GSC Connector.

        Args:
            site_url: The site URL registered in Search Console.
            credentials_path: Path to service account credentials JSON file.
            credentials_json: Service account credentials as dictionary.
        """
        self.site_url = site_url
        self.credentials_path = credentials_path
        self.credentials_json = credentials_json
        self._service = None
        self._mock_mode = False
        self._mock_data: List[Dict[str, Any]] = []

    def _get_credentials(self):
        """Get OAuth2 credentials for GSC API."""
        try:
            from google.oauth2 import service_account

            scopes = ["https://www.googleapis.com/auth/webmasters.readonly"]

            if self.credentials_path:
                return service_account.Credentials.from_service_account_file(
                    self.credentials_path, scopes=scopes
                )
            elif self.credentials_json:
                return service_account.Credentials.from_service_account_info(
                    self.credentials_json, scopes=scopes
                )
            else:
                # Use default credentials (e.g., from environment)
                import google.auth

                credentials, _ = google.auth.default(scopes=scopes)
                return credentials
        except Exception as e:
            logger.error(f"Failed to get GSC credentials: {e}")
            raise

    def _get_service(self):
        """Get or create the GSC API service."""
        if self._mock_mode:
            return None

        if self._service is None:
            try:
                from googleapiclient.discovery import build

                credentials = self._get_credentials()
                self._service = build("searchconsole", "v1", credentials=credentials)
            except ImportError:
                logger.warning(
                    "google-api-python-client package not installed, using mock mode"
                )
                self._mock_mode = True
            except Exception as e:
                logger.error(f"Failed to initialize GSC service: {e}")
                self._mock_mode = True

        return self._service

    def enable_mock_mode(self, mock_data: Optional[List[Dict[str, Any]]] = None):
        """Enable mock mode for testing."""
        self._mock_mode = True
        self._mock_data = mock_data or []

    async def get_performance_data(
        self,
        start_date: str,
        end_date: str,
        dimensions: Optional[List[str]] = None,
        row_limit: int = 25000,
    ) -> List[Dict[str, Any]]:
        """
        Get performance data from Google Search Console.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            dimensions: List of dimensions (page, query, date, country, device).
            row_limit: Maximum number of rows to return.

        Returns:
            List of performance data rows with clicks, impressions, position, and ctr.
        """
        if self._mock_mode:
            logger.debug("Using mock GSC data")
            return self._mock_data

        service = self._get_service()
        if service is None:
            return []

        try:
            request = {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": dimensions or ["page", "query"],
                "rowLimit": row_limit,
            }

            response = (
                service.searchanalytics()
                .query(siteUrl=self.site_url, body=request)
                .execute()
            )

            return self._parse_response(response, dimensions or ["page", "query"])
        except Exception as e:
            logger.error(f"Failed to fetch GSC performance data: {e}")
            raise

    def _parse_response(
        self, response: Dict[str, Any], dimensions: List[str]
    ) -> List[Dict[str, Any]]:
        """Parse GSC API response into list of dictionaries."""
        rows = response.get("rows", [])
        results = []

        for row in rows:
            result = {
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": row.get("ctr", 0.0),
                "position": row.get("position", 0.0),
            }

            # Add dimension keys
            keys = row.get("keys", [])
            for i, dim in enumerate(dimensions):
                if i < len(keys):
                    result[dim] = keys[i]

            results.append(result)

        return results

    async def get_page_performance(
        self, start_date: str, end_date: str, page_url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get page-level performance data.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            page_url: Optional specific page URL to filter by.

        Returns:
            List of page performance metrics.
        """
        if self._mock_mode:
            return self._mock_data

        service = self._get_service()
        if service is None:
            return []

        try:
            request = {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": ["page"],
                "rowLimit": 25000,
            }

            if page_url:
                request["dimensionFilterGroups"] = [
                    {
                        "filters": [
                            {
                                "dimension": "page",
                                "operator": "equals",
                                "expression": page_url,
                            }
                        ]
                    }
                ]

            response = (
                service.searchanalytics()
                .query(siteUrl=self.site_url, body=request)
                .execute()
            )

            return self._parse_response(response, ["page"])
        except Exception as e:
            logger.error(f"Failed to fetch GSC page performance: {e}")
            raise

    async def get_query_performance(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Get query-level performance data.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            List of query performance metrics.
        """
        if self._mock_mode:
            return self._mock_data

        service = self._get_service()
        if service is None:
            return []

        try:
            request = {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": ["query"],
                "rowLimit": 25000,
            }

            response = (
                service.searchanalytics()
                .query(siteUrl=self.site_url, body=request)
                .execute()
            )

            return self._parse_response(response, ["query"])
        except Exception as e:
            logger.error(f"Failed to fetch GSC query performance: {e}")
            raise

    async def get_daily_performance(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Get daily performance time series.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            List of daily performance metrics.
        """
        if self._mock_mode:
            return self._mock_data

        service = self._get_service()
        if service is None:
            return []

        try:
            request = {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": ["date"],
                "rowLimit": 25000,
            }

            response = (
                service.searchanalytics()
                .query(siteUrl=self.site_url, body=request)
                .execute()
            )

            return self._parse_response(response, ["date"])
        except Exception as e:
            logger.error(f"Failed to fetch GSC daily performance: {e}")
            raise
