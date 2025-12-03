"""Google Trends Connector for trending keyword discovery."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class GoogleTrendsConnector:
    """Connector for Google Trends data.

    Uses pytrends library (unofficial API) to get trending searches
    and interest over time data.
    """

    def __init__(self):
        """Initialize Google Trends connector."""
        self._pytrends = None
        self._initialized = False

    def _init_pytrends(self):
        """Lazily initialize pytrends to avoid import errors if not installed."""
        if self._initialized:
            return

        try:
            from pytrends.request import TrendReq
            self._pytrends = TrendReq(hl="en-US", tz=360)
            self._initialized = True
        except ImportError:
            logger.warning("pytrends not installed, using mock data")
            self._initialized = True
        except Exception as e:
            logger.warning(f"Failed to initialize pytrends: {e}, using mock data")
            self._initialized = True

    async def get_trending_searches(
        self, geo: str = "US", category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get daily trending searches from Google Trends.

        Args:
            geo: Geographic region code (default: US)
            category: Optional category filter

        Returns:
            List of trending keywords with metadata
        """
        self._init_pytrends()

        if self._pytrends is None:
            logger.warning("pytrends not available, returning mock data")
            return self._get_mock_trending_searches(geo)

        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            trending_df = await loop.run_in_executor(
                None, lambda: self._pytrends.trending_searches(pn=geo.lower())
            )

            if trending_df is None or trending_df.empty:
                return []

            trends = []
            for idx, row in trending_df.head(20).iterrows():
                keyword = row[0] if len(row) > 0 else str(row)
                trends.append({
                    "keyword": keyword,
                    "rank": idx + 1,
                    "source": "google_trends",
                    "geo": geo,
                    "fetched_at": datetime.utcnow().isoformat(),
                })

            return trends
        except Exception as e:
            logger.error(f"Error fetching Google Trends data: {e}")
            return self._get_mock_trending_searches(geo)

    async def get_interest_over_time(
        self,
        keyword: str,
        timeframe: str = "today 3-m",
        geo: str = "US",
    ) -> Dict[str, Any]:
        """Get interest over time for a keyword.

        Args:
            keyword: The keyword to analyze
            timeframe: Time range (e.g., 'today 3-m', 'today 12-m')
            geo: Geographic region code

        Returns:
            Dictionary with trend data and score
        """
        self._init_pytrends()

        if self._pytrends is None:
            logger.warning("pytrends not available, returning mock data")
            return self._get_mock_interest_over_time(keyword)

        try:
            loop = asyncio.get_event_loop()

            # Build payload in executor
            await loop.run_in_executor(
                None,
                lambda: self._pytrends.build_payload(
                    [keyword], timeframe=timeframe, geo=geo
                ),
            )

            # Get interest over time
            interest_df = await loop.run_in_executor(
                None, self._pytrends.interest_over_time
            )

            if interest_df is None or interest_df.empty:
                return {
                    "keyword": keyword,
                    "trend_score": 0,
                    "trend_data": [],
                    "source": "google_trends",
                }

            # Calculate average interest as trend score
            if keyword in interest_df.columns:
                values = interest_df[keyword].tolist()
                trend_score = int(sum(values) / len(values)) if values else 0

                trend_data = [
                    {"date": str(date), "value": int(val)}
                    for date, val in zip(interest_df.index, values)
                ]

                return {
                    "keyword": keyword,
                    "trend_score": trend_score,
                    "trend_data": trend_data[-30:],  # Last 30 data points
                    "source": "google_trends",
                }

            return {
                "keyword": keyword,
                "trend_score": 0,
                "trend_data": [],
                "source": "google_trends",
            }
        except Exception as e:
            logger.error(f"Error fetching interest over time: {e}")
            return self._get_mock_interest_over_time(keyword)

    async def get_related_queries(
        self, keyword: str, geo: str = "US"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get related queries for a keyword.

        Args:
            keyword: The seed keyword
            geo: Geographic region code

        Returns:
            Dictionary with 'top' and 'rising' related queries
        """
        self._init_pytrends()

        if self._pytrends is None:
            return self._get_mock_related_queries(keyword)

        try:
            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None,
                lambda: self._pytrends.build_payload(
                    [keyword], timeframe="today 3-m", geo=geo
                ),
            )

            related = await loop.run_in_executor(
                None, self._pytrends.related_queries
            )

            if related is None or keyword not in related:
                return {"top": [], "rising": []}

            result = {"top": [], "rising": []}

            # Process top queries
            top_df = related[keyword].get("top")
            if top_df is not None and not top_df.empty:
                result["top"] = [
                    {"query": row["query"], "value": int(row["value"])}
                    for _, row in top_df.head(10).iterrows()
                ]

            # Process rising queries
            rising_df = related[keyword].get("rising")
            if rising_df is not None and not rising_df.empty:
                result["rising"] = [
                    {"query": row["query"], "value": str(row["value"])}
                    for _, row in rising_df.head(10).iterrows()
                ]

            return result
        except Exception as e:
            logger.error(f"Error fetching related queries: {e}")
            return self._get_mock_related_queries(keyword)

    def _get_mock_trending_searches(self, geo: str) -> List[Dict[str, Any]]:
        """Generate mock trending searches for testing."""
        mock_trends = [
            "artificial intelligence",
            "machine learning tutorial",
            "python programming",
            "web development",
            "cloud computing",
            "data science",
            "cybersecurity",
            "blockchain technology",
            "remote work tips",
            "productivity tools",
        ]

        return [
            {
                "keyword": trend,
                "rank": i + 1,
                "source": "google_trends_mock",
                "geo": geo,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            for i, trend in enumerate(mock_trends)
        ]

    def _get_mock_interest_over_time(self, keyword: str) -> Dict[str, Any]:
        """Generate mock interest over time data for testing."""
        seed = sum(ord(c) for c in keyword)
        base_date = datetime.now(timezone.utc) - timedelta(days=30)

        trend_data = [
            {
                "date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                "value": (seed * (i + 1) * 7) % 100,
            }
            for i in range(30)
        ]

        avg_score = sum(d["value"] for d in trend_data) // len(trend_data)

        return {
            "keyword": keyword,
            "trend_score": avg_score,
            "trend_data": trend_data,
            "source": "google_trends_mock",
        }

    def _get_mock_related_queries(
        self, keyword: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate mock related queries for testing."""
        return {
            "top": [
                {"query": f"{keyword} tutorial", "value": 100},
                {"query": f"{keyword} examples", "value": 85},
                {"query": f"best {keyword}", "value": 70},
                {"query": f"{keyword} guide", "value": 60},
                {"query": f"{keyword} for beginners", "value": 50},
            ],
            "rising": [
                {"query": f"{keyword} 2024", "value": "Breakout"},
                {"query": f"{keyword} trends", "value": "+500%"},
                {"query": f"{keyword} tools", "value": "+250%"},
            ],
        }
