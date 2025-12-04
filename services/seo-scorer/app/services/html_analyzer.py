"""HTML Analyzer for automatic SEO analysis.

This module provides functionality to analyze HTML content for SEO factors
using BeautifulSoup for parsing.
"""

import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.core.constants import (
    MIN_KEYWORD_DENSITY,
    MAX_KEYWORD_DENSITY,
    MIN_WORD_COUNT,
)


class HTMLAnalyzer:
    """Analyzer for extracting SEO-related data from HTML content."""

    # Default internal domain patterns (can be configured per workspace)
    DEFAULT_INTERNAL_PATTERNS = [
        r"^/",  # Relative URLs
        r"^#",  # Anchor links
    ]

    def __init__(self, internal_domain: Optional[str] = None):
        """Initialize the HTML analyzer.

        Args:
            internal_domain: The internal domain for identifying internal links.
        """
        self.internal_domain = internal_domain

    def analyze(
        self, html_content: str, target_keywords: List[str]
    ) -> Dict:
        """Analyze HTML content for SEO factors.

        Args:
            html_content: The HTML content to analyze.
            target_keywords: List of target keywords to check for.

        Returns:
            Dictionary containing SEO analysis results.
        """
        if not html_content:
            return self._empty_analysis()

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract all relevant data
        title = soup.find("title")
        title_text = title.get_text().strip() if title else ""

        h1_tags = soup.find_all("h1")
        h2_tags = soup.find_all("h2")

        # Get all text content
        body = soup.find("body")
        if body:
            text_content = body.get_text(separator=" ", strip=True)
        else:
            text_content = soup.get_text(separator=" ", strip=True)

        words = text_content.split()
        word_count = len(words)

        # Analyze images
        images = soup.find_all("img")
        images_data = self._analyze_images(images)

        # Analyze links
        links = soup.find_all("a", href=True)
        internal_links, external_links = self._analyze_links(links)

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_desc.get("content", "") if meta_desc else ""

        # Keyword analysis
        keywords_lower = [kw.lower() for kw in target_keywords]
        keyword_in_title = self._check_keywords_in_text(title_text, keywords_lower)
        keyword_in_h1 = any(
            self._check_keywords_in_text(h1.get_text(), keywords_lower)
            for h1 in h1_tags
        )
        keyword_in_h2 = any(
            self._check_keywords_in_text(h2.get_text(), keywords_lower)
            for h2 in h2_tags
        )
        keyword_density = self._calculate_keyword_density(text_content, keywords_lower)

        return {
            "title_contains_keyword": keyword_in_title,
            "h1_present": len(h1_tags) > 0,
            "h1_count": len(h1_tags),
            "h1_contains_keyword": keyword_in_h1,
            "h2_count": len(h2_tags),
            "h2_contains_keyword": keyword_in_h2,
            "keyword_density": keyword_density,
            "keyword_density_ok": MIN_KEYWORD_DENSITY <= keyword_density <= MAX_KEYWORD_DENSITY,
            "images_count": len(images),
            "images_with_alt": images_data["with_alt"],
            "images_without_alt": images_data["without_alt"],
            "images_have_alt": images_data["all_have_alt"],
            "word_count": word_count,
            "word_count_adequate": word_count >= MIN_WORD_COUNT,
            "internal_links": len(internal_links),
            "external_links": len(external_links),
            "has_internal_links": len(internal_links) > 0,
            "has_external_links": len(external_links) > 0,
            "meta_description": len(meta_description) > 0,
            "meta_description_length": len(meta_description),
            "title_length": len(title_text),
            "score": 0,  # Will be calculated by AutoScorer
        }

    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure."""
        return {
            "title_contains_keyword": False,
            "h1_present": False,
            "h1_count": 0,
            "h1_contains_keyword": False,
            "h2_count": 0,
            "h2_contains_keyword": False,
            "keyword_density": 0.0,
            "keyword_density_ok": False,
            "images_count": 0,
            "images_with_alt": 0,
            "images_without_alt": 0,
            "images_have_alt": True,  # No images = no missing alt tags
            "word_count": 0,
            "word_count_adequate": False,
            "internal_links": 0,
            "external_links": 0,
            "has_internal_links": False,
            "has_external_links": False,
            "meta_description": False,
            "meta_description_length": 0,
            "title_length": 0,
            "score": 0,
        }

    def _check_keywords_in_text(self, text: str, keywords: List[str]) -> bool:
        """Check if any keyword is present in text.

        Args:
            text: The text to search in.
            keywords: List of keywords (lowercase) to search for.

        Returns:
            True if at least one keyword is found.
        """
        if not text or not keywords:
            return False

        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)

    def _calculate_keyword_density(
        self, text: str, keywords: List[str]
    ) -> float:
        """Calculate keyword density as percentage.

        Args:
            text: The text content.
            keywords: List of keywords (lowercase).

        Returns:
            Keyword density as percentage.
        """
        if not text or not keywords:
            return 0.0

        words = text.lower().split()
        total_words = len(words)

        if total_words == 0:
            return 0.0

        keyword_count = 0
        for word in words:
            # Clean word for better matching
            clean_word = re.sub(r"[^\w]", "", word)
            if any(kw in clean_word for kw in keywords):
                keyword_count += 1

        return round((keyword_count / total_words) * 100, 2)

    def _analyze_images(self, images) -> Dict:
        """Analyze images for alt tag presence.

        Args:
            images: List of image tags from BeautifulSoup.

        Returns:
            Dictionary with image analysis data.
        """
        with_alt = 0
        without_alt = 0

        for img in images:
            alt = img.get("alt", "").strip()
            if alt:
                with_alt += 1
            else:
                without_alt += 1

        return {
            "with_alt": with_alt,
            "without_alt": without_alt,
            "all_have_alt": without_alt == 0,
        }

    def _analyze_links(self, links) -> tuple:
        """Analyze links to classify as internal or external.

        Args:
            links: List of anchor tags from BeautifulSoup.

        Returns:
            Tuple of (internal_links, external_links) lists.
        """
        internal_links = []
        external_links = []

        for link in links:
            href = link.get("href", "")
            if self._is_internal_link(href):
                internal_links.append(href)
            else:
                external_links.append(href)

        return internal_links, external_links

    def _is_internal_link(self, href: str) -> bool:
        """Check if a link is internal.

        Args:
            href: The href attribute value.

        Returns:
            True if the link is internal.
        """
        if not href:
            return False

        # Check for relative URLs and anchor links
        if href.startswith("/") or href.startswith("#"):
            return True

        # Check for javascript: links (considered internal)
        if href.startswith("javascript:"):
            return True

        # Check for mailto: and tel: (neither internal nor external)
        if href.startswith("mailto:") or href.startswith("tel:"):
            return False

        # If internal domain is set, check against it
        if self.internal_domain:
            try:
                parsed = urlparse(href)
                return parsed.netloc == self.internal_domain
            except Exception:
                return False

        # Default: assume external if has http/https
        if href.startswith("http://") or href.startswith("https://"):
            return False

        return True
