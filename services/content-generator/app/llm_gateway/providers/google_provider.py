"""Google Generative AI (Gemini) LLM Provider implementation."""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.llm_gateway.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)
settings = get_settings()


# Pricing per 1K tokens (as of late 2024)
GOOGLE_PRICING = {
    "gemini-1.5-pro": {"input": Decimal("0.00125"), "output": Decimal("0.005")},
    "gemini-1.5-flash": {"input": Decimal("0.000075"), "output": Decimal("0.0003")},
    "gemini-pro": {"input": Decimal("0.0005"), "output": Decimal("0.0015")},
}


class GoogleProvider(LLMProvider):
    """Google Generative AI (Gemini) provider."""

    provider_name = "google"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Google provider.

        Args:
            api_key: Google API key. If not provided, uses settings.
        """
        self.api_key = api_key or getattr(settings, "GOOGLE_API_KEY", "")
        self.client = None
        self._default_model = "gemini-1.5-pro"

        # Only import google-generativeai if we have an API key
        if self.api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self.genai = genai
                self.client = True  # Flag to indicate configured
            except ImportError:
                logger.warning("google-generativeai package not installed")

    @property
    def is_available(self) -> bool:
        """Check if Google AI is available."""
        return bool(self.api_key and self.client)

    def get_available_models(self) -> List[str]:
        """Get available Google models."""
        return list(GOOGLE_PRICING.keys())

    def get_default_model(self) -> str:
        """Get default model."""
        return self._default_model

    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> Decimal:
        """Calculate cost for Google API usage."""
        pricing = GOOGLE_PRICING.get(model, GOOGLE_PRICING["gemini-1.5-pro"])
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
        """Generate content using Google Generative AI API."""
        if not self.client:
            logger.warning("Google API key not configured, returning mock response")
            return self._generate_mock_response(prompt, model)

        model_to_use = model or self._default_model

        try:
            gen_model = self.genai.GenerativeModel(model_to_use)

            # Combine system prompt and user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            generation_config = self.genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # Use synchronous generate_content and wrap in async
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: gen_model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                ),
            )

            content = response.text if response.text else ""

            # Google doesn't always provide token counts, estimate if needed
            usage_metadata = getattr(response, "usage_metadata", None)
            if usage_metadata:
                input_tokens = getattr(usage_metadata, "prompt_token_count", None)
                output_tokens = getattr(usage_metadata, "candidates_token_count", None)
                if input_tokens is None:
                    input_tokens = len(full_prompt.split()) * 2
                if output_tokens is None:
                    output_tokens = len(content.split()) * 2
            else:
                input_tokens = len(full_prompt.split()) * 2
                output_tokens = len(content.split()) * 2

            cost = self.calculate_cost(input_tokens, output_tokens, model_to_use)

            return LLMResponse(
                content=content,
                model=model_to_use,
                provider=self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=cost,
                metadata={"finish_reason": "completed"},
            )
        except Exception as e:
            logger.error(f"Google API error: {e}")
            raise

    def _generate_mock_response(self, prompt: str, model: Optional[str]) -> LLMResponse:
        """Generate mock response for testing."""
        model_to_use = model or self._default_model
        mock_content = f"Mock Google Gemini response for: {prompt[:100]}..."
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
