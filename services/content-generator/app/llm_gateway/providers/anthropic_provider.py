"""Anthropic Claude LLM Provider implementation."""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.llm_gateway.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)
settings = get_settings()


# Pricing per 1K tokens (as of late 2024)
ANTHROPIC_PRICING = {
    "claude-3-5-sonnet-20241022": {"input": Decimal("0.003"), "output": Decimal("0.015")},
    "claude-3-sonnet-20240229": {"input": Decimal("0.003"), "output": Decimal("0.015")},
    "claude-3-opus-20240229": {"input": Decimal("0.015"), "output": Decimal("0.075")},
    "claude-3-haiku-20240307": {"input": Decimal("0.00025"), "output": Decimal("0.00125")},
}


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    provider_name = "anthropic"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key. If not provided, uses settings.
        """
        self.api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", "")
        self.client = None
        self._default_model = "claude-3-5-sonnet-20241022"

        # Only import anthropic if we have an API key
        if self.api_key:
            try:
                import anthropic

                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("anthropic package not installed")

    @property
    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return bool(self.api_key and self.client)

    def get_available_models(self) -> List[str]:
        """Get available Anthropic models."""
        return list(ANTHROPIC_PRICING.keys())

    def get_default_model(self) -> str:
        """Get default model."""
        return self._default_model

    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> Decimal:
        """Calculate cost for Anthropic API usage."""
        pricing = ANTHROPIC_PRICING.get(model, ANTHROPIC_PRICING["claude-3-5-sonnet-20241022"])
        input_cost = (Decimal(input_tokens) / 1000) * pricing["input"]
        output_cost = (Decimal(output_tokens) / 1000) * pricing["output"]
        return input_cost + output_cost

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate content using Anthropic API."""
        if not self.client:
            logger.warning("Anthropic API key not configured, returning mock response")
            return self._generate_mock_response(prompt, model)

        model_to_use = model or self._default_model

        try:
            kwargs: Dict[str, Any] = {
                "model": model_to_use,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self.client.messages.create(**kwargs)

            content = response.content[0].text if response.content else ""
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self.calculate_cost(input_tokens, output_tokens, model_to_use)

            return LLMResponse(
                content=content,
                model=model_to_use,
                provider=self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=cost,
                metadata={"stop_reason": response.stop_reason},
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def _generate_mock_response(self, prompt: str, model: Optional[str]) -> LLMResponse:
        """Generate mock response for testing."""
        model_to_use = model or self._default_model
        mock_content = f"Mock Anthropic response for: {prompt[:100]}..."
        mock_input = len(prompt.split()) * 2
        mock_output = len(mock_content.split()) * 2

        return LLMResponse(
            content=mock_content,
            model=f"{model_to_use}-mock",
            provider=self.provider_name,
            input_tokens=mock_input,
            output_tokens=mock_output,
            total_tokens=mock_input + mock_output,
            cost_usd=self.calculate_cost(mock_input, mock_output, model_to_use),
            metadata={"mock": True},
        )
