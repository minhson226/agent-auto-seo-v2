"""AI-powered anchor text rewriter."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnchorTextRewriter:
    """Service for AI-powered anchor text rewriting.

    Rewrites sentences to naturally include anchor text for internal links
    using LLM generation.
    """

    def __init__(
        self,
        llm_gateway=None,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        mock_mode: bool = False,
    ):
        """Initialize the Anchor Text Rewriter.

        Args:
            llm_gateway: LLM Gateway instance for generation
            provider: LLM provider to use (openai, anthropic, etc.)
            model: Model name to use
            mock_mode: If True, return mock responses
        """
        self._llm_gateway = llm_gateway
        self._provider = provider
        self._model = model
        self._mock_mode = mock_mode
        self._mock_responses: List[Dict[str, Any]] = []

    @property
    def mock_mode(self) -> bool:
        """Check if rewriter is in mock mode."""
        return self._mock_mode

    @property
    def mock_responses(self) -> List[Dict[str, Any]]:
        """Get list of mock responses (for testing)."""
        return self._mock_responses

    def clear_mock_responses(self) -> None:
        """Clear mock responses (for testing)."""
        self._mock_responses = []

    async def rewrite_sentence_with_link(
        self,
        sentence: str,
        keyword: str,
        target_url: str,
    ) -> str:
        """Rewrite a sentence to naturally include a link with anchor text.

        Args:
            sentence: The original sentence to rewrite
            keyword: The keyword to use as anchor text
            target_url: The URL to link to

        Returns:
            Rewritten sentence with HTML link included
        """
        if self._mock_mode:
            # Create a simple mock response
            rewritten = self._create_mock_rewrite(sentence, keyword, target_url)
            self._mock_responses.append({
                "original": sentence,
                "keyword": keyword,
                "target_url": target_url,
                "rewritten": rewritten,
            })
            return rewritten

        if not self._llm_gateway:
            logger.warning("LLM Gateway not available for rewriting")
            # Fallback: simple replacement with link
            return self._simple_link_insertion(sentence, keyword, target_url)

        try:
            prompt = f"""Rewrite this sentence to naturally include a link with anchor text "{keyword}":

Original: {sentence}

Requirements:
- Keep the original meaning intact
- Make the link placement feel natural
- Use "{keyword}" as the anchor text exactly
- Return only the rewritten sentence with HTML link

Example output format: 'This is a sentence with <a href="url">anchor text</a> in it.'
"""

            response = await self._llm_gateway.generate(
                prompt=prompt,
                provider=self._provider,
                model=self._model,
                temperature=0.3,
                max_tokens=500,
            )

            rewritten = response.content.strip()

            # Verify the link is properly formatted
            if f'<a href="{target_url}">' not in rewritten:
                # If the model forgot the URL, fix it
                rewritten = rewritten.replace(
                    f'<a href="url">{keyword}</a>',
                    f'<a href="{target_url}">{keyword}</a>',
                )

            return rewritten

        except Exception as e:
            logger.error(f"Failed to rewrite sentence: {e}")
            return self._simple_link_insertion(sentence, keyword, target_url)

    def _simple_link_insertion(
        self,
        sentence: str,
        keyword: str,
        target_url: str,
    ) -> str:
        """Simple fallback link insertion without AI.

        Args:
            sentence: The original sentence
            keyword: The keyword to link
            target_url: The URL to link to

        Returns:
            Sentence with link inserted
        """
        import re

        # Case-insensitive replacement of the keyword with a link
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        link_html = f'<a href="{target_url}">{keyword}</a>'

        # Replace only the first occurrence
        return pattern.sub(link_html, sentence, count=1)

    def _create_mock_rewrite(
        self,
        sentence: str,
        keyword: str,
        target_url: str,
    ) -> str:
        """Create a mock rewritten sentence for testing.

        Args:
            sentence: The original sentence
            keyword: The keyword to link
            target_url: The URL to link to

        Returns:
            Mock rewritten sentence
        """
        return self._simple_link_insertion(sentence, keyword, target_url)

    async def rewrite_multiple_sentences(
        self,
        sentences: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Rewrite multiple sentences with links.

        Args:
            sentences: List of dicts with 'sentence', 'keyword', 'target_url'

        Returns:
            List of dicts with original and rewritten sentences
        """
        results = []
        for item in sentences:
            rewritten = await self.rewrite_sentence_with_link(
                sentence=item["sentence"],
                keyword=item["keyword"],
                target_url=item["target_url"],
            )
            results.append({
                "original": item["sentence"],
                "keyword": item["keyword"],
                "target_url": item["target_url"],
                "rewritten": rewritten,
            })
        return results

    async def suggest_anchor_text(
        self,
        article_title: str,
        article_content: str,
        target_keywords: List[str],
    ) -> List[str]:
        """Suggest appropriate anchor text for an article.

        Args:
            article_title: Title of the target article
            article_content: Content of the target article
            target_keywords: Keywords associated with the article

        Returns:
            List of suggested anchor texts, best first
        """
        if self._mock_mode:
            # Return keywords and title as suggestions
            suggestions = target_keywords.copy() if target_keywords else []
            if article_title and article_title not in suggestions:
                suggestions.insert(0, article_title)
            return suggestions[:5]

        if not self._llm_gateway:
            # Fallback to keywords and title
            suggestions = target_keywords.copy() if target_keywords else []
            if article_title:
                suggestions.insert(0, article_title)
            return suggestions[:5]

        try:
            prompt = f"""Based on this article, suggest 5 appropriate anchor texts for internal links to this article.

Title: {article_title}
Target Keywords: {', '.join(target_keywords) if target_keywords else 'None'}
Content Preview: {article_content[:500]}...

Requirements:
- Anchor texts should be concise (2-5 words)
- They should accurately describe the article
- Include variations for natural linking
- List them in order of preference

Return only the anchor texts, one per line."""

            response = await self._llm_gateway.generate(
                prompt=prompt,
                provider=self._provider,
                model=self._model,
                temperature=0.3,
                max_tokens=200,
            )

            suggestions = [
                line.strip().strip("-").strip("•").strip()
                for line in response.content.strip().split("\n")
                if line.strip()
            ]
            return suggestions[:5]

        except Exception as e:
            logger.error(f"Failed to suggest anchor texts: {e}")
            suggestions = target_keywords.copy() if target_keywords else []
            if article_title:
                suggestions.insert(0, article_title)
            return suggestions[:5]
