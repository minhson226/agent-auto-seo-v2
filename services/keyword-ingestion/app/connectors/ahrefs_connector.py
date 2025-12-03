"""Ahrefs API Connector for keyword research and competitor analysis."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AhrefsConnector:
    """Connector for Ahrefs API.

    Provides methods to get keyword metrics, related keywords,
    and competitor keyword analysis.
    """

    BASE_URL = "https://api.ahrefs.com/v3"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Ahrefs connector.

        Args:
            api_key: Ahrefs API key. If not provided, uses settings.
        """
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "AHREFS_API_KEY", "")
        self.timeout = httpx.Timeout(30.0)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def get_keyword_metrics(
        self, keyword: str, country: str = "us"
    ) -> Dict[str, Any]:
        """Get keyword metrics from Ahrefs.

        Args:
            keyword: The keyword to analyze
            country: Country code for localized data (default: us)

        Returns:
            Dictionary with search_volume, keyword_difficulty, cpc, clicks
        """
        if not self.api_key:
            logger.warning("Ahrefs API key not configured, returning mock data")
            return self._get_mock_keyword_metrics(keyword)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/keywords-explorer/keyword-metrics",
                    headers=self._get_headers(),
                    params={
                        "keyword": keyword,
                        "country": country,
                    },
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "search_volume": data.get("search_volume", 0),
                    "keyword_difficulty": data.get("keyword_difficulty", 0),
                    "cpc": data.get("cpc", 0.0),
                    "clicks": data.get("clicks", 0),
                    "source": "ahrefs",
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"Ahrefs API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Ahrefs keyword metrics: {e}")
            raise

    async def get_related_keywords(
        self, keyword: str, country: str = "us", limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get related keywords from Ahrefs.

        Args:
            keyword: The seed keyword
            country: Country code for localized data
            limit: Maximum number of related keywords to return

        Returns:
            List of related keywords with metrics
        """
        if not self.api_key:
            logger.warning("Ahrefs API key not configured, returning mock data")
            return self._get_mock_related_keywords(keyword, limit)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/keywords-explorer/related-terms",
                    headers=self._get_headers(),
                    params={
                        "keyword": keyword,
                        "country": country,
                        "limit": limit,
                    },
                )
                response.raise_for_status()
                data = response.json()

                return [
                    {
                        "keyword": kw.get("keyword", ""),
                        "search_volume": kw.get("search_volume", 0),
                        "keyword_difficulty": kw.get("keyword_difficulty", 0),
                        "cpc": kw.get("cpc", 0.0),
                    }
                    for kw in data.get("keywords", [])[:limit]
                ]
        except httpx.HTTPStatusError as e:
            logger.error(f"Ahrefs API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Ahrefs related keywords: {e}")
            raise

    async def get_competitor_keywords(
        self, domain: str, country: str = "us", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get keywords that a competitor ranks for.

        Args:
            domain: Competitor domain to analyze
            country: Country code for localized data
            limit: Maximum number of keywords to return

        Returns:
            List of keywords with ranking data
        """
        if not self.api_key:
            logger.warning("Ahrefs API key not configured, returning mock data")
            return self._get_mock_competitor_keywords(domain, limit)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/site-explorer/organic-keywords",
                    headers=self._get_headers(),
                    params={
                        "target": domain,
                        "country": country,
                        "limit": limit,
                        "mode": "domain",
                    },
                )
                response.raise_for_status()
                data = response.json()

                return [
                    {
                        "keyword": kw.get("keyword", ""),
                        "search_volume": kw.get("search_volume", 0),
                        "position": kw.get("position", 0),
                        "traffic": kw.get("traffic", 0),
                        "url": kw.get("url", ""),
                    }
                    for kw in data.get("keywords", [])[:limit]
                ]
        except httpx.HTTPStatusError as e:
            logger.error(f"Ahrefs API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Ahrefs competitor keywords: {e}")
            raise

    def _get_mock_keyword_metrics(self, keyword: str) -> Dict[str, Any]:
        """Generate mock keyword metrics for testing without API key."""
        # Generate pseudo-random but deterministic metrics based on keyword
        seed = sum(ord(c) for c in keyword)
        return {
            "search_volume": (seed * 123) % 10000 + 100,
            "keyword_difficulty": (seed * 7) % 100,
            "cpc": round(((seed * 13) % 500) / 100, 2),
            "clicks": (seed * 89) % 5000,
            "source": "ahrefs_mock",
        }

    def _get_mock_related_keywords(
        self, keyword: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Generate mock related keywords for testing."""
        prefixes = ["best", "top", "how to", "what is", "buy"]
        suffixes = ["guide", "tips", "review", "2024", "near me"]
        related = []

        for i, prefix in enumerate(prefixes[:limit]):
            related.append({
                "keyword": f"{prefix} {keyword}",
                "search_volume": (i + 1) * 500,
                "keyword_difficulty": (i + 1) * 10,
                "cpc": round((i + 1) * 0.5, 2),
            })

        for i, suffix in enumerate(suffixes[:max(0, limit - len(prefixes))]):
            related.append({
                "keyword": f"{keyword} {suffix}",
                "search_volume": (i + 1) * 300,
                "keyword_difficulty": (i + 1) * 8,
                "cpc": round((i + 1) * 0.4, 2),
            })

        return related[:limit]

    def _get_mock_competitor_keywords(
        self, domain: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Generate mock competitor keywords for testing."""
        base_keywords = [
            "product review",
            "best practices",
            "how to guide",
            "tutorial",
            "comparison",
        ]
        return [
            {
                "keyword": f"{domain.split('.')[0]} {kw}",
                "search_volume": (i + 1) * 400,
                "position": i + 1,
                "traffic": (i + 1) * 100,
                "url": f"https://{domain}/{kw.replace(' ', '-')}",
            }
            for i, kw in enumerate(base_keywords[:limit])
        ]
