"""XAI (Grok) LLM Provider implementation."""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.llm_gateway.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)
settings = get_settings()


# Pricing per 1K tokens (as of late 2024)
XAI_PRICING = {
    "grok-beta": {"input": Decimal("0.005"), "output": Decimal("0.015")},
    "grok-2": {"input": Decimal("0.002"), "output": Decimal("0.01")},
}


class XAIProvider(LLMProvider):
    """XAI (Grok) API provider.

    Uses OpenAI-compatible API endpoint.
    """

    provider_name = "xai"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize XAI provider.

        Args:
            api_key: XAI API key. If not provided, uses settings.
        """
        self.api_key = api_key or getattr(settings, "XAI_API_KEY", "")
        self.client = None
        self._default_model = "grok-beta"

        # XAI uses OpenAI-compatible API
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.x.ai/v1",
            )

    @property
    def is_available(self) -> bool:
        """Check if XAI is available."""
        return bool(self.api_key and self.client)

    def get_available_models(self) -> List[str]:
        """Get available XAI models."""
        return list(XAI_PRICING.keys())

    def get_default_model(self) -> str:
        """Get default model."""
        return self._default_model

    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> Decimal:
        """Calculate cost for XAI API usage."""
        pricing = XAI_PRICING.get(model, XAI_PRICING["grok-beta"])
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
        """Generate content using XAI API."""
        if not self.client:
            logger.warning("XAI API key not configured, returning mock response")
            return self._generate_mock_response(prompt, model)

        model_to_use = model or self._default_model
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content or ""
            usage = response.usage

            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            cost = self.calculate_cost(input_tokens, output_tokens, model_to_use)

            return LLMResponse(
                content=content,
                model=model_to_use,
                provider=self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=cost,
                metadata={"finish_reason": response.choices[0].finish_reason},
            )
        except Exception as e:
            logger.error(f"XAI API error: {e}")
            raise

    def _generate_mock_response(self, prompt: str, model: Optional[str]) -> LLMResponse:
        """Generate mock response for testing."""
        model_to_use = model or self._default_model
        mock_content = f"Mock XAI Grok response for: {prompt[:100]}..."
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
