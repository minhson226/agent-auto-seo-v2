"""Keyword processor service for normalization and deduplication."""

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)


class KeywordProcessor:
    """Processor for normalizing and deduplicating keywords."""

    def normalize(self, keyword: str) -> str:
        """Normalize keyword: lowercase, trim, remove extra spaces.

        Args:
            keyword: Raw keyword string

        Returns:
            Normalized keyword string
        """
        # Lowercase
        normalized = keyword.lower()

        # Trim leading/trailing whitespace
        normalized = normalized.strip()

        # Replace multiple spaces with single space
        normalized = " ".join(normalized.split())

        return normalized

    def deduplicate(self, keywords: List[str]) -> List[Tuple[str, str]]:
        """Remove duplicates after normalization.

        Args:
            keywords: List of raw keywords

        Returns:
            List of tuples (original_text, normalized_text) with duplicates removed
        """
        seen = set()
        unique = []

        for kw in keywords:
            normalized = self.normalize(kw)

            # Skip empty keywords after normalization
            if not normalized:
                continue

            if normalized not in seen:
                seen.add(normalized)
                unique.append((kw, normalized))

        logger.info(
            f"Deduplicated {len(keywords)} keywords to {len(unique)} unique keywords"
        )
        return unique

    def process(self, keywords: List[str]) -> List[Tuple[str, str]]:
        """Process keywords: normalize and deduplicate.

        Args:
            keywords: List of raw keywords

        Returns:
            List of tuples (original_text, normalized_text)
        """
        return self.deduplicate(keywords)
