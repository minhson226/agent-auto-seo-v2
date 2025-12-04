"""LLM Gateway - Multi-provider LLM abstraction layer."""

import logging
from typing import Dict, List, Optional, Type

from app.llm_gateway.providers.base import LLMProvider, LLMResponse
from app.llm_gateway.providers.openai_provider import OpenAIProvider
from app.llm_gateway.providers.anthropic_provider import AnthropicProvider
from app.llm_gateway.providers.google_provider import GoogleProvider
from app.llm_gateway.providers.xai_provider import XAIProvider

logger = logging.getLogger(__name__)


class LLMGateway:
    """Gateway for accessing multiple LLM providers.

    Provides a unified interface for generating content using different LLM
    providers (OpenAI, Anthropic, Google, XAI/Grok).
    """

    def __init__(self):
        """Initialize the LLM Gateway with all providers."""
        self.providers: Dict[str, LLMProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "google": GoogleProvider(),
            "xai": XAIProvider(),
        }

    def get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """Get a specific provider by name.

        Args:
            provider_name: Name of the provider (openai, anthropic, google, xai)

        Returns:
            The provider instance or None if not found
        """
        return self.providers.get(provider_name)

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names.

        Returns:
            List of provider names that are configured and available
        """
        return [name for name, provider in self.providers.items() if provider.is_available]

    def get_all_providers(self) -> List[str]:
        """Get list of all provider names (including unavailable).

        Returns:
            List of all provider names
        """
        return list(self.providers.keys())

    async def generate(
        self,
        prompt: str,
        provider: str = "openai",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate content using the specified provider.

        Args:
            prompt: The user prompt to generate content from
            provider: Name of the provider to use (default: openai)
            model: Optional specific model to use
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            ValueError: If the provider is not found
        """
        llm_provider = self.providers.get(provider)
        if not llm_provider:
            raise ValueError(f"Provider '{provider}' not found. Available: {list(self.providers.keys())}")

        logger.info(f"Generating content using provider: {provider}, model: {model or 'default'}")

        response = await llm_provider.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(
            f"Generated {response.total_tokens} tokens using {response.model}, "
            f"cost: ${response.cost_usd}"
        )

        return response

    def get_provider_models(self, provider: str) -> List[str]:
        """Get available models for a specific provider.

        Args:
            provider: Name of the provider

        Returns:
            List of available model names
        """
        llm_provider = self.providers.get(provider)
        if not llm_provider:
            return []
        return llm_provider.get_available_models()


# Global gateway instance
llm_gateway = LLMGateway()
