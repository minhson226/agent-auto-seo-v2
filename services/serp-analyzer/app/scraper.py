"""SERP Scraper for retrieving search engine results."""

import asyncio
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin, urlparse

logger = logging.getLogger(__name__)


@dataclass
class SERPResult:
    """Represents a single SERP result."""

    position: int
    url: str
    title: str
    description: str
    domain: str


class SERPScraper:
    """Scraper for retrieving top search results.

    Supports multiple methods:
    1. Google Custom Search API (recommended, requires API key)
    2. ScraperAPI (alternative, requires API key)
    3. Direct scraping (not recommended, may get blocked)
    """

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_cse_id: Optional[str] = None,
        scraper_api_key: Optional[str] = None,
    ):
        """Initialize the SERP scraper.

        Args:
            google_api_key: Google Custom Search API key
            google_cse_id: Google Custom Search Engine ID
            scraper_api_key: ScraperAPI API key
        """
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY")
        self.google_cse_id = google_cse_id or os.environ.get("GOOGLE_CSE_ID")
        self.scraper_api_key = scraper_api_key or os.environ.get("SCRAPER_API_KEY")

        self._http_client = None

    async def _get_client(self):
        """Get or create HTTP client."""
        if self._http_client is None:
            import httpx

            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
            )
        return self._http_client

    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def get_top_results(
        self,
        keyword: str,
        num_results: int = 10,
        country: str = "us",
        language: str = "en",
    ) -> List[SERPResult]:
        """Get top search results for a keyword.

        Tries methods in order of preference:
        1. Google Custom Search API
        2. ScraperAPI
        3. Mock data (for testing/development)

        Args:
            keyword: Search keyword
            num_results: Number of results to retrieve (max 10 per request)
            country: Country code for localized results
            language: Language code

        Returns:
            List of SERP results
        """
        # Try Google Custom Search API first
        if self.google_api_key and self.google_cse_id:
            try:
                return await self._search_google_api(
                    keyword, num_results, country, language
                )
            except Exception as e:
                logger.warning(f"Google API search failed: {e}")

        # Try ScraperAPI
        if self.scraper_api_key:
            try:
                return await self._search_scraper_api(
                    keyword, num_results, country, language
                )
            except Exception as e:
                logger.warning(f"ScraperAPI search failed: {e}")

        # Return mock data for development/testing
        logger.warning("No API keys configured, returning mock SERP data")
        return self._get_mock_results(keyword, num_results)

    async def _search_google_api(
        self,
        keyword: str,
        num_results: int,
        country: str,
        language: str,
    ) -> List[SERPResult]:
        """Search using Google Custom Search API.

        Args:
            keyword: Search query
            num_results: Number of results
            country: Country code
            language: Language code

        Returns:
            List of SERP results
        """
        client = await self._get_client()

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cse_id,
            "q": keyword,
            "num": min(num_results, 10),  # Max 10 per request
            "gl": country,
            "hl": language,
        }

        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        results = []
        items = data.get("items", [])
        for idx, item in enumerate(items):
            url = item.get("link", "")
            results.append(
                SERPResult(
                    position=idx + 1,
                    url=url,
                    title=item.get("title", ""),
                    description=item.get("snippet", ""),
                    domain=urlparse(url).netloc,
                )
            )

        return results

    async def _search_scraper_api(
        self,
        keyword: str,
        num_results: int,
        country: str,
        language: str,
    ) -> List[SERPResult]:
        """Search using ScraperAPI.

        Args:
            keyword: Search query
            num_results: Number of results
            country: Country code
            language: Language code

        Returns:
            List of SERP results
        """
        client = await self._get_client()

        # Build Google search URL
        google_url = f"https://www.google.com/search?q={quote_plus(keyword)}&num={num_results}&hl={language}&gl={country}"

        # Use ScraperAPI to fetch
        url = f"http://api.scraperapi.com?api_key={self.scraper_api_key}&url={quote_plus(google_url)}"

        response = await client.get(url)
        response.raise_for_status()
        html = response.text

        # Parse results from HTML
        return self._parse_google_html(html)

    def _parse_google_html(self, html: str) -> List[SERPResult]:
        """Parse Google search results from HTML.

        Args:
            html: Raw HTML from Google search

        Returns:
            List of SERP results
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Find organic search results
            # Note: Google's HTML structure changes frequently
            search_results = soup.select("div.g")

            for idx, result in enumerate(search_results[:10]):
                # Extract URL
                link = result.find("a")
                if not link or not link.get("href"):
                    continue

                url = link.get("href", "")
                if url.startswith("/url?q="):
                    url = url.split("/url?q=")[1].split("&")[0]

                # Extract title
                title_elem = result.find("h3")
                title = title_elem.get_text() if title_elem else ""

                # Extract description
                desc_elem = result.find("div", class_="VwiC3b")
                description = desc_elem.get_text() if desc_elem else ""

                if url and title:
                    results.append(
                        SERPResult(
                            position=idx + 1,
                            url=url,
                            title=title,
                            description=description,
                            domain=urlparse(url).netloc,
                        )
                    )

            return results

        except ImportError:
            logger.error("BeautifulSoup required for HTML parsing")
            return []

    def _get_mock_results(
        self,
        keyword: str,
        num_results: int,
    ) -> List[SERPResult]:
        """Generate mock SERP results for testing.

        Args:
            keyword: Search keyword
            num_results: Number of results

        Returns:
            List of mock SERP results
        """
        mock_domains = [
            "example.com",
            "competitor1.com",
            "competitor2.com",
            "wikipedia.org",
            "medium.com",
            "blog.example.com",
            "guide.example.com",
            "tutorial.io",
            "learn.example.org",
            "howto.example.net",
        ]

        results = []
        for i in range(min(num_results, len(mock_domains))):
            domain = mock_domains[i]
            slug = keyword.lower().replace(" ", "-")
            results.append(
                SERPResult(
                    position=i + 1,
                    url=f"https://{domain}/{slug}",
                    title=f"{keyword.title()} - Guide by {domain.split('.')[0].title()}",
                    description=f"Learn everything about {keyword}. Complete guide and tutorial...",
                    domain=domain,
                )
            )

        return results

    async def get_search_suggestions(
        self,
        keyword: str,
        country: str = "us",
    ) -> List[str]:
        """Get autocomplete/search suggestions for a keyword.

        Args:
            keyword: Base keyword
            country: Country code

        Returns:
            List of suggested searches
        """
        client = await self._get_client()

        try:
            url = "https://suggestqueries.google.com/complete/search"
            params = {
                "client": "firefox",
                "q": keyword,
                "hl": country,
            }

            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Response format: [query, [suggestions]]
            if isinstance(data, list) and len(data) > 1:
                return data[1]
            return []

        except Exception as e:
            logger.warning(f"Failed to get search suggestions: {e}")
            return []

    async def get_related_searches(
        self,
        keyword: str,
    ) -> List[str]:
        """Get related searches for a keyword.

        Note: Requires scraping Google results page.

        Args:
            keyword: Base keyword

        Returns:
            List of related searches
        """
        # For now, return suggestions as related searches
        # Full implementation would parse "related searches" from SERP HTML
        suggestions = await self.get_search_suggestions(keyword)
        return suggestions[:5]


# Singleton instance
_serp_scraper: Optional[SERPScraper] = None


def get_serp_scraper(
    google_api_key: Optional[str] = None,
    google_cse_id: Optional[str] = None,
    scraper_api_key: Optional[str] = None,
) -> SERPScraper:
    """Get or create the SERP scraper instance.

    Args:
        google_api_key: Google Custom Search API key
        google_cse_id: Google Custom Search Engine ID
        scraper_api_key: ScraperAPI key

    Returns:
        SERPScraper instance
    """
    global _serp_scraper
    if _serp_scraper is None:
        _serp_scraper = SERPScraper(
            google_api_key=google_api_key,
            google_cse_id=google_cse_id,
            scraper_api_key=scraper_api_key,
        )
    return _serp_scraper
