"""Tests for LLM Gateway functionality."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.llm_gateway import LLMGateway, CostRouter, LLMProvider, LLMResponse
from app.llm_gateway.providers.openai_provider import OpenAIProvider
from app.llm_gateway.providers.anthropic_provider import AnthropicProvider
from app.llm_gateway.providers.google_provider import GoogleProvider
from app.llm_gateway.providers.xai_provider import XAIProvider


class TestLLMGateway:
    """Tests for LLMGateway class."""

    def test_gateway_initialization(self):
        """Test LLM Gateway initializes with all providers."""
        gateway = LLMGateway()

        assert "openai" in gateway.providers
        assert "anthropic" in gateway.providers
        assert "google" in gateway.providers
        assert "xai" in gateway.providers

    def test_get_all_providers(self):
        """Test getting all provider names."""
        gateway = LLMGateway()
        providers = gateway.get_all_providers()

        assert len(providers) >= 4
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers
        assert "xai" in providers

    def test_get_provider(self):
        """Test getting a specific provider."""
        gateway = LLMGateway()

        openai = gateway.get_provider("openai")
        assert openai is not None
        assert openai.provider_name == "openai"

        unknown = gateway.get_provider("unknown")
        assert unknown is None

    def test_get_provider_models(self):
        """Test getting models for a provider."""
        gateway = LLMGateway()

        openai_models = gateway.get_provider_models("openai")
        assert len(openai_models) >= 1
        assert "gpt-4o" in openai_models

        unknown_models = gateway.get_provider_models("unknown")
        assert len(unknown_models) == 0

    @pytest.mark.asyncio
    async def test_generate_mock_response(self):
        """Test generating mock response when no API key is configured."""
        gateway = LLMGateway()

        # Without API keys, providers return mock responses
        response = await gateway.generate(
            prompt="Test prompt",
            provider="openai",
        )

        assert response.content is not None
        assert response.provider == "openai"
        assert "-mock" in response.model
        assert response.total_tokens > 0

    @pytest.mark.asyncio
    async def test_generate_invalid_provider(self):
        """Test generation with invalid provider raises error."""
        gateway = LLMGateway()

        with pytest.raises(ValueError) as exc_info:
            await gateway.generate(
                prompt="Test prompt",
                provider="invalid_provider",
            )

        assert "not found" in str(exc_info.value)


class TestCostRouter:
    """Tests for CostRouter class."""

    def test_select_model_high_priority(self):
        """Test model selection for high priority."""
        router = CostRouter()
        provider, model = router.select_model(priority="high")

        assert provider == "openai"
        assert model == "gpt-4o"

    def test_select_model_medium_priority(self):
        """Test model selection for medium priority."""
        router = CostRouter()
        provider, model = router.select_model(priority="medium")

        assert provider == "anthropic"
        assert "claude" in model.lower()

    def test_select_model_low_priority(self):
        """Test model selection for low priority."""
        router = CostRouter()
        provider, model = router.select_model(priority="low")

        assert provider == "google"
        assert "gemini" in model.lower()

    def test_select_model_with_budget_constraint(self):
        """Test model selection with budget constraint."""
        router = CostRouter()

        # Very low budget should select cheapest option
        selection = router.get_model_selection(
            priority="high",
            word_count=1000,
            max_budget_usd=0.001,  # Very low budget
        )

        # Should find a cheaper model
        assert selection.estimated_cost_per_1k_tokens <= 0.01

    def test_get_model_selection_details(self):
        """Test getting detailed model selection."""
        router = CostRouter()

        selection = router.get_model_selection(priority="medium")

        assert selection.provider is not None
        assert selection.model is not None
        assert selection.estimated_cost_per_1k_tokens > 0
        assert selection.reason is not None

    def test_estimate_cost(self):
        """Test cost estimation."""
        router = CostRouter()

        cost = router.estimate_cost(
            provider="openai",
            model="gpt-4o",
            word_count=1000,
        )

        # Cost should be positive
        assert cost > 0

    def test_invalid_priority_defaults_to_medium(self):
        """Test invalid priority defaults to medium."""
        router = CostRouter()

        selection = router.get_model_selection(priority="invalid")

        # Should default to medium priority route
        assert selection.provider == "anthropic" or selection.provider == "openai"


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    def test_available_models(self):
        """Test OpenAI available models."""
        provider = OpenAIProvider(api_key="test")

        models = provider.get_available_models()
        assert "gpt-4o" in models
        assert "gpt-3.5-turbo" in models

    def test_default_model(self):
        """Test OpenAI default model."""
        provider = OpenAIProvider(api_key="test")
        assert provider.get_default_model() == "gpt-4o"

    def test_calculate_cost(self):
        """Test cost calculation."""
        provider = OpenAIProvider(api_key="test")

        cost = provider.calculate_cost(
            input_tokens=1000,
            output_tokens=1000,
            model="gpt-4o",
        )

        assert cost > Decimal("0")

    @pytest.mark.asyncio
    async def test_generate_mock_without_api_key(self):
        """Test mock generation without API key."""
        provider = OpenAIProvider(api_key="")

        response = await provider.generate(
            prompt="Test prompt",
        )

        assert "-mock" in response.model
        assert response.provider == "openai"


class TestAnthropicProvider:
    """Tests for Anthropic provider."""

    def test_available_models(self):
        """Test Anthropic available models."""
        provider = AnthropicProvider(api_key="")

        models = provider.get_available_models()
        assert len(models) >= 1
        assert any("claude" in m.lower() for m in models)

    def test_calculate_cost(self):
        """Test cost calculation."""
        provider = AnthropicProvider(api_key="")

        cost = provider.calculate_cost(
            input_tokens=1000,
            output_tokens=1000,
            model="claude-3-5-sonnet-20241022",
        )

        assert cost > Decimal("0")

    @pytest.mark.asyncio
    async def test_generate_mock_without_api_key(self):
        """Test mock generation without API key."""
        provider = AnthropicProvider(api_key="")

        response = await provider.generate(
            prompt="Test prompt",
        )

        assert "-mock" in response.model
        assert response.provider == "anthropic"


class TestGoogleProvider:
    """Tests for Google provider."""

    def test_available_models(self):
        """Test Google available models."""
        provider = GoogleProvider(api_key="")

        models = provider.get_available_models()
        assert len(models) >= 1
        assert any("gemini" in m.lower() for m in models)

    @pytest.mark.asyncio
    async def test_generate_mock_without_api_key(self):
        """Test mock generation without API key."""
        provider = GoogleProvider(api_key="")

        response = await provider.generate(
            prompt="Test prompt",
        )

        assert "-mock" in response.model
        assert response.provider == "google"


class TestXAIProvider:
    """Tests for XAI/Grok provider."""

    def test_available_models(self):
        """Test XAI available models."""
        provider = XAIProvider(api_key="")

        models = provider.get_available_models()
        assert len(models) >= 1
        assert any("grok" in m.lower() for m in models)

    @pytest.mark.asyncio
    async def test_generate_mock_without_api_key(self):
        """Test mock generation without API key."""
        provider = XAIProvider(api_key="")

        response = await provider.generate(
            prompt="Test prompt",
        )

        assert "-mock" in response.model
        assert response.provider == "xai"
