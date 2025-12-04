"""Content Analyzer for extracting metrics from competitor pages."""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


@dataclass
class ContentMetrics:
    """Metrics extracted from a web page."""

    url: str
    word_count: int = 0
    h1: Optional[str] = None
    h2_count: int = 0
    h3_count: int = 0
    h2_headings: List[str] = field(default_factory=list)
    h3_headings: List[str] = field(default_factory=list)
    images_count: int = 0
    images_with_alt: int = 0
    internal_links: int = 0
    external_links: int = 0
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    schema_types: List[str] = field(default_factory=list)
    readability_score: float = 0.0


class ContentAnalyzer:
    """Analyzes competitor content to extract SEO-relevant metrics."""

    def __init__(self):
        """Initialize the content analyzer."""
        self._http_client = None

    async def _get_client(self):
        """Get or create HTTP client."""
        if self._http_client is None:
            import httpx

            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
        return self._http_client

    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page's HTML content.

        Args:
            url: URL to fetch

        Returns:
            HTML content or None if fetch failed
        """
        client = await self._get_client()

        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    async def analyze_content(self, url: str) -> Optional[ContentMetrics]:
        """Analyze a single URL for content metrics.

        Args:
            url: URL to analyze

        Returns:
            ContentMetrics object or None if analysis failed
        """
        html = await self.fetch_page(url)
        if not html:
            return None

        return self._extract_metrics(url, html)

    def _extract_metrics(self, url: str, html: str) -> ContentMetrics:
        """Extract metrics from HTML content.

        Args:
            url: Source URL
            html: HTML content

        Returns:
            ContentMetrics object
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            metrics = ContentMetrics(url=url)

            # Remove script and style elements
            for element in soup(["script", "style", "noscript"]):
                element.decompose()

            # Word count (from main content)
            body = soup.find("body")
            if body:
                text = body.get_text(separator=" ", strip=True)
                words = text.split()
                metrics.word_count = len(words)

            # H1
            h1 = soup.find("h1")
            metrics.h1 = h1.get_text(strip=True) if h1 else None

            # H2 headings
            h2s = soup.find_all("h2")
            metrics.h2_count = len(h2s)
            metrics.h2_headings = [h.get_text(strip=True) for h in h2s[:10]]

            # H3 headings
            h3s = soup.find_all("h3")
            metrics.h3_count = len(h3s)
            metrics.h3_headings = [h.get_text(strip=True) for h in h3s[:10]]

            # Images
            images = soup.find_all("img")
            metrics.images_count = len(images)
            metrics.images_with_alt = sum(1 for img in images if img.get("alt"))

            # Links
            links = soup.find_all("a", href=True)
            for link in links:
                href = link.get("href", "")
                if self._is_internal_link(href, domain):
                    metrics.internal_links += 1
                elif href.startswith(("http://", "https://")):
                    metrics.external_links += 1

            # Meta tags
            meta_title = soup.find("title")
            metrics.meta_title = meta_title.get_text(strip=True) if meta_title else None

            meta_desc = soup.find("meta", attrs={"name": "description"})
            metrics.meta_description = (
                meta_desc.get("content") if meta_desc else None
            )

            # Schema.org types
            schema_elements = soup.find_all("script", type="application/ld+json")
            schema_types: Set[str] = set()
            for elem in schema_elements:
                try:
                    import json

                    data = json.loads(elem.string or "")
                    if isinstance(data, dict):
                        if "@type" in data:
                            schema_types.add(data["@type"])
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "@type" in item:
                                schema_types.add(item["@type"])
                except (json.JSONDecodeError, TypeError):
                    pass
            metrics.schema_types = list(schema_types)

            # Simple readability score (based on average sentence length)
            sentences = re.split(r"[.!?]+", text if body else "")
            if sentences:
                avg_sentence_length = metrics.word_count / max(len(sentences), 1)
                # Flesch-like approximation (lower is more complex)
                metrics.readability_score = max(
                    0, min(100, 206.835 - 1.015 * avg_sentence_length)
                )

            return metrics

        except ImportError:
            logger.error("BeautifulSoup required for content analysis")
            return ContentMetrics(url=url)

    def _is_internal_link(self, href: str, domain: str) -> bool:
        """Check if a link is internal to the domain.

        Args:
            href: Link href attribute
            domain: Current domain

        Returns:
            True if internal link
        """
        if not href:
            return False
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            return False
        if href.startswith("/"):
            return True
        if domain in href:
            return True
        return False

    async def analyze_multiple(
        self,
        urls: List[str],
        max_concurrent: int = 5,
    ) -> List[ContentMetrics]:
        """Analyze multiple URLs concurrently.

        Args:
            urls: List of URLs to analyze
            max_concurrent: Maximum concurrent requests

        Returns:
            List of ContentMetrics objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(url: str) -> Optional[ContentMetrics]:
            async with semaphore:
                return await self.analyze_content(url)

        tasks = [analyze_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        metrics = []
        for result in results:
            if isinstance(result, ContentMetrics):
                metrics.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Analysis failed: {result}")

        return metrics

    def aggregate_metrics(
        self,
        metrics_list: List[ContentMetrics],
    ) -> Dict[str, Any]:
        """Aggregate metrics from multiple pages.

        Args:
            metrics_list: List of ContentMetrics objects

        Returns:
            Aggregated statistics
        """
        if not metrics_list:
            return {}

        word_counts = [m.word_count for m in metrics_list]
        h2_counts = [m.h2_count for m in metrics_list]
        h3_counts = [m.h3_count for m in metrics_list]
        image_counts = [m.images_count for m in metrics_list]
        internal_links = [m.internal_links for m in metrics_list]
        external_links = [m.external_links for m in metrics_list]

        # Collect all headings
        all_h2s = []
        all_h3s = []
        for m in metrics_list:
            all_h2s.extend(m.h2_headings)
            all_h3s.extend(m.h3_headings)

        # Find common heading patterns
        h2_counter: Dict[str, int] = {}
        for h2 in all_h2s:
            h2_lower = h2.lower()
            h2_counter[h2_lower] = h2_counter.get(h2_lower, 0) + 1

        common_headings = [
            h for h, count in sorted(h2_counter.items(), key=lambda x: -x[1])
            if count >= 2
        ][:10]

        return {
            "count": len(metrics_list),
            "avg_word_count": sum(word_counts) / len(word_counts),
            "min_word_count": min(word_counts),
            "max_word_count": max(word_counts),
            "avg_h2_count": sum(h2_counts) / len(h2_counts),
            "avg_h3_count": sum(h3_counts) / len(h3_counts),
            "avg_images": sum(image_counts) / len(image_counts),
            "avg_internal_links": sum(internal_links) / len(internal_links),
            "avg_external_links": sum(external_links) / len(external_links),
            "common_headings": common_headings,
            "analyzed_urls": [m.url for m in metrics_list],
        }

    async def analyze_competitors(
        self,
        urls: List[str],
    ) -> Dict[str, Any]:
        """Analyze competitor URLs and return aggregated insights.

        Args:
            urls: List of competitor URLs

        Returns:
            Dictionary with aggregated competitor insights
        """
        metrics = await self.analyze_multiple(urls)
        aggregated = self.aggregate_metrics(metrics)

        # Add recommendations based on analysis
        recommendations = []

        avg_word_count = aggregated.get("avg_word_count", 0)
        if avg_word_count:
            target_words = int(avg_word_count * 1.2)
            recommendations.append(
                f"Aim for {target_words:,} words (20% more than competitor average)"
            )

        avg_h2 = aggregated.get("avg_h2_count", 0)
        if avg_h2:
            recommendations.append(
                f"Use approximately {int(avg_h2)} H2 headings"
            )

        avg_images = aggregated.get("avg_images", 0)
        if avg_images:
            recommendations.append(
                f"Include {int(avg_images)} or more images"
            )

        aggregated["recommendations"] = recommendations

        return aggregated


# Singleton instance
_content_analyzer: Optional[ContentAnalyzer] = None


def get_content_analyzer() -> ContentAnalyzer:
    """Get or create the content analyzer instance.

    Returns:
        ContentAnalyzer instance
    """
    global _content_analyzer
    if _content_analyzer is None:
        _content_analyzer = ContentAnalyzer()
    return _content_analyzer
