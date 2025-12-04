"""Base LLM Provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: Decimal
    metadata: Dict[str, Any]


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    provider_name: str = "base"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate content using the LLM.

        Args:
            prompt: The user prompt to generate content from
            model: Optional specific model to use
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with generated content and metadata
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider.

        Returns:
            List of model names
        """
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this provider.

        Returns:
            Default model name
        """
        pass

    @abstractmethod
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> Decimal:
        """Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: The model used

        Returns:
            Cost in USD as Decimal
        """
        pass

    @property
    def is_available(self) -> bool:
        """Check if the provider is available (has valid API key).

        Returns:
            True if provider can be used
        """
        return True
