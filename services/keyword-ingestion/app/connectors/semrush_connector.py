"""SEMrush API Connector for keyword research."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SEMrushConnector:
    """Connector for SEMrush API.

    Provides methods to get keyword overview and related keywords.
    """

    BASE_URL = "https://api.semrush.com"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize SEMrush connector.

        Args:
            api_key: SEMrush API key. If not provided, uses settings.
        """
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "SEMRUSH_API_KEY", "")
        self.timeout = httpx.Timeout(30.0)

    async def get_keyword_overview(
        self, keyword: str, database: str = "us"
    ) -> Dict[str, Any]:
        """Get keyword overview from SEMrush (Phrase Report).

        Args:
            keyword: The keyword to analyze
            database: SEMrush database code (default: us)

        Returns:
            Dictionary with search_volume, cpc, competition, etc.
        """
        if not self.api_key:
            logger.warning("SEMrush API key not configured, returning mock data")
            return self._get_mock_keyword_overview(keyword)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/",
                    params={
                        "type": "phrase_this",
                        "key": self.api_key,
                        "phrase": keyword,
                        "database": database,
                        "export_columns": "Ph,Nq,Cp,Co,Nr,Td",
                    },
                )
                response.raise_for_status()

                # SEMrush returns CSV-like data
                lines = response.text.strip().split("\n")
                if len(lines) < 2:
                    return self._get_empty_overview()

                # Parse header and data
                headers = lines[0].split(";")
                values = lines[1].split(";")

                data = dict(zip(headers, values))

                return {
                    "keyword": data.get("Keyword", keyword),
                    "search_volume": int(data.get("Search Volume", 0)),
                    "cpc": float(data.get("CPC", 0.0)),
                    "competition": float(data.get("Competition", 0.0)),
                    "results_count": int(data.get("Number of Results", 0)),
                    "trend": data.get("Trend", ""),
                    "source": "semrush",
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"SEMrush API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error fetching SEMrush keyword overview: {e}")
            raise

    async def get_related_keywords(
        self, keyword: str, database: str = "us", limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get related keywords from SEMrush.

        Args:
            keyword: The seed keyword
            database: SEMrush database code
            limit: Maximum number of related keywords to return

        Returns:
            List of related keywords with metrics
        """
        if not self.api_key:
            logger.warning("SEMrush API key not configured, returning mock data")
            return self._get_mock_related_keywords(keyword, limit)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/",
                    params={
                        "type": "phrase_related",
                        "key": self.api_key,
                        "phrase": keyword,
                        "database": database,
                        "display_limit": limit,
                        "export_columns": "Ph,Nq,Cp,Co",
                    },
                )
                response.raise_for_status()

                # Parse CSV response
                lines = response.text.strip().split("\n")
                if len(lines) < 2:
                    return []

                headers = lines[0].split(";")
                results = []

                for line in lines[1:limit + 1]:
                    values = line.split(";")
                    if len(values) >= len(headers):
                        data = dict(zip(headers, values))
                        results.append({
                            "keyword": data.get("Keyword", ""),
                            "search_volume": int(data.get("Search Volume", 0)),
                            "cpc": float(data.get("CPC", 0.0)),
                            "competition": float(data.get("Competition", 0.0)),
                        })

                return results
        except httpx.HTTPStatusError as e:
            logger.error(f"SEMrush API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error fetching SEMrush related keywords: {e}")
            raise

    async def get_keyword_difficulty(
        self, keyword: str, database: str = "us"
    ) -> Dict[str, Any]:
        """Get keyword difficulty score from SEMrush.

        Args:
            keyword: The keyword to analyze
            database: SEMrush database code

        Returns:
            Dictionary with difficulty score and related metrics
        """
        if not self.api_key:
            logger.warning("SEMrush API key not configured, returning mock data")
            seed = sum(ord(c) for c in keyword)
            return {
                "keyword": keyword,
                "difficulty": (seed * 7) % 100,
                "source": "semrush_mock",
            }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/",
                    params={
                        "type": "phrase_kdi",
                        "key": self.api_key,
                        "phrase": keyword,
                        "database": database,
                    },
                )
                response.raise_for_status()

                lines = response.text.strip().split("\n")
                if len(lines) < 2:
                    return {"keyword": keyword, "difficulty": 0, "source": "semrush"}

                headers = lines[0].split(";")
                values = lines[1].split(";")
                data = dict(zip(headers, values))

                return {
                    "keyword": keyword,
                    "difficulty": float(data.get("Keyword Difficulty Index", 0)),
                    "source": "semrush",
                }
        except Exception as e:
            logger.error(f"Error fetching SEMrush keyword difficulty: {e}")
            raise

    def _get_empty_overview(self) -> Dict[str, Any]:
        """Return empty overview structure."""
        return {
            "keyword": "",
            "search_volume": 0,
            "cpc": 0.0,
            "competition": 0.0,
            "results_count": 0,
            "trend": "",
            "source": "semrush",
        }

    def _get_mock_keyword_overview(self, keyword: str) -> Dict[str, Any]:
        """Generate mock keyword overview for testing."""
        seed = sum(ord(c) for c in keyword)
        return {
            "keyword": keyword,
            "search_volume": (seed * 97) % 10000 + 100,
            "cpc": round(((seed * 17) % 500) / 100, 2),
            "competition": round(((seed * 31) % 100) / 100, 2),
            "results_count": (seed * 12345) % 1000000,
            "trend": "0.8,0.9,1.0,1.1,1.0,0.9,1.0,1.1,1.2,1.0,0.9,1.0",
            "source": "semrush_mock",
        }

    def _get_mock_related_keywords(
        self, keyword: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Generate mock related keywords for testing."""
        modifiers = ["best", "cheap", "online", "free", "new", "top", "how to", "buy"]
        related = []

        for i, mod in enumerate(modifiers[:limit]):
            seed = sum(ord(c) for c in f"{mod}{keyword}")
            related.append({
                "keyword": f"{mod} {keyword}",
                "search_volume": (seed * 37) % 5000 + 50,
                "cpc": round(((seed * 11) % 400) / 100, 2),
                "competition": round(((seed * 23) % 100) / 100, 2),
            })

        return related
