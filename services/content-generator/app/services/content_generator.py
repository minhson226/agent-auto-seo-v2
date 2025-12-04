"""Content Generator service using OpenAI API."""

import logging
import re
from decimal import Decimal
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.schemas.article import GenerationResult

logger = logging.getLogger(__name__)
settings = get_settings()

# GPT-3.5-turbo pricing (as of late 2023)
# Input: $0.0015 per 1K tokens, Output: $0.002 per 1K tokens
PRICING_INPUT_PER_1K = Decimal("0.0015")
PRICING_OUTPUT_PER_1K = Decimal("0.002")


class ContentGenerator:
    """Content generator using OpenAI GPT-3.5."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the content generator."""
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE

    async def generate_article(
        self,
        title: str,
        target_keywords: List[str],
        estimated_word_count: Optional[int] = None,
    ) -> GenerationResult:
        """Generate an SEO article based on content plan details.

        Args:
            title: The article title
            target_keywords: List of target keywords to include
            estimated_word_count: Target word count for the article

        Returns:
            GenerationResult with content, cost, and metadata
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")

        prompt = self._build_prompt(title, target_keywords, estimated_word_count)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert SEO content writer. "
                        "You write comprehensive, engaging, and well-structured articles "
                        "that rank well in search engines while providing value to readers."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        # Calculate cost
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        cost = self._calculate_cost(input_tokens, output_tokens)

        # Count words
        word_count = self._count_words(content)

        return GenerationResult(
            content=content,
            cost_usd=cost,
            model=self.model,
            word_count=word_count,
            tokens_used={
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
        )

    def _build_prompt(
        self,
        title: str,
        target_keywords: List[str],
        estimated_word_count: Optional[int] = None,
    ) -> str:
        """Build the prompt for article generation.

        Args:
            title: The article title
            target_keywords: List of target keywords
            estimated_word_count: Target word count

        Returns:
            Formatted prompt string
        """
        word_count_str = str(estimated_word_count) if estimated_word_count else "1500-2000"
        keywords_str = ", ".join(target_keywords) if target_keywords else "relevant terms"

        return f"""
Write a comprehensive SEO article about: {title}

Target keywords: {keywords_str}
Estimated word count: {word_count_str}

Requirements:
- Include H1 title with main keyword at the beginning
- Include H2 and H3 subheadings to organize content
- Naturally incorporate target keywords throughout the article
- Write in an engaging, informative style that provides real value
- Include a compelling introduction that hooks the reader
- Include a clear conclusion with a call to action
- Use short paragraphs and bullet points where appropriate
- Include relevant examples and explanations
- Format the output in Markdown

Output the article in Markdown format with proper heading structure.
"""

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate the cost of API usage.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used

        Returns:
            Cost in USD as Decimal
        """
        input_cost = (Decimal(input_tokens) / 1000) * PRICING_INPUT_PER_1K
        output_cost = (Decimal(output_tokens) / 1000) * PRICING_OUTPUT_PER_1K
        return input_cost + output_cost

    def _count_words(self, text: str) -> int:
        """Count words in text.

        Args:
            text: The text to count words in

        Returns:
            Number of words
        """
        # Remove markdown formatting
        clean_text = re.sub(r"[#*`\[\]()]", "", text)
        words = clean_text.split()
        return len(words)


# Global instance
content_generator = ContentGenerator()
