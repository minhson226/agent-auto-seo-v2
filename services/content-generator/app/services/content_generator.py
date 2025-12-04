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
    """Content generator using OpenAI GPT-3.5.

    When no API key is configured (empty string or not set), the generator
    falls back to returning mock content for testing purposes.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the content generator.

        Args:
            api_key: OpenAI API key. If not provided, uses settings.OPENAI_API_KEY.
                     If empty string, mock mode is enabled.
        """
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        # Only create client if we have a non-empty API key
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

        When no OpenAI API key is configured, returns mock content suitable
        for testing. This allows CI to run without real API credentials.

        Args:
            title: The article title
            target_keywords: List of target keywords to include
            estimated_word_count: Target word count for the article

        Returns:
            GenerationResult with content, cost, and metadata
        """
        # If no client (no API key), return mock content for testing
        if not self.client:
            logger.warning("OpenAI API key not configured, returning mock content")
            return self._generate_mock_article(title, target_keywords, estimated_word_count)

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

    def _generate_mock_article(
        self,
        title: str,
        target_keywords: List[str],
        estimated_word_count: Optional[int] = None,
    ) -> GenerationResult:
        """Generate mock article content for testing without API key.

        Args:
            title: The article title
            target_keywords: List of target keywords
            estimated_word_count: Target word count

        Returns:
            GenerationResult with mock content
        """
        keywords_str = ", ".join(target_keywords) if target_keywords else "relevant topics"
        word_count = estimated_word_count or 1500

        # Generate deterministic mock content based on title
        content = f"""# {title}

## Introduction

This is a comprehensive guide about {title}. In this article, we will explore the key aspects
of {keywords_str} and provide valuable insights for our readers.

## Understanding the Basics

When it comes to {title.lower()}, there are several important factors to consider. The first
step is to understand the fundamental concepts that drive success in this area.

### Key Concepts

- **Concept One**: An important foundation for understanding {keywords_str}
- **Concept Two**: Building upon the basics to achieve better results
- **Concept Three**: Advanced strategies for optimization

## Best Practices

Following industry best practices is essential for success. Here are some proven strategies:

1. Start with a solid foundation
2. Focus on quality over quantity
3. Continuously measure and improve
4. Stay updated with the latest trends

## Practical Tips

Here are some actionable tips you can implement right away:

- Research thoroughly before starting
- Create a structured plan
- Execute consistently
- Review and refine your approach

## Conclusion

In conclusion, mastering {title.lower()} requires dedication and the right approach.
By following the guidelines in this article, you can achieve excellent results.

We hope this guide helps you on your journey. Feel free to reach out with any questions!
"""

        # Calculate mock tokens (approximate)
        mock_prompt_tokens = len(title.split()) * 5 + len(target_keywords) * 3 + 100
        mock_completion_tokens = len(content.split()) * 2
        mock_cost = self._calculate_cost(mock_prompt_tokens, mock_completion_tokens)

        return GenerationResult(
            content=content,
            cost_usd=mock_cost,
            model=f"{self.model}-mock",
            word_count=self._count_words(content),
            tokens_used={
                "prompt_tokens": mock_prompt_tokens,
                "completion_tokens": mock_completion_tokens,
                "total_tokens": mock_prompt_tokens + mock_completion_tokens,
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
