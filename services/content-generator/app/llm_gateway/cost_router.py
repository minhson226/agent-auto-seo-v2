"""Cost Optimization Router for LLM model selection."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Content generation priority levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ModelSelection:
    """Selected model and provider information."""

    provider: str
    model: str
    estimated_cost_per_1k_tokens: float
    reason: str


class CostRouter:
    """Cost optimization router for selecting the best model based on requirements.

    Routes requests to different LLM providers/models based on:
    - Priority level (high/medium/low)
    - Word count / complexity
    - Budget constraints
    - Model availability
    """

    # Default model mappings for each priority
    DEFAULT_ROUTES = {
        Priority.HIGH: ("openai", "gpt-4o"),
        Priority.MEDIUM: ("anthropic", "claude-3-5-sonnet-20241022"),
        Priority.LOW: ("google", "gemini-1.5-flash"),
    }

    # Fallback routes if primary provider is unavailable
    FALLBACK_ROUTES = {
        Priority.HIGH: [
            ("anthropic", "claude-3-opus-20240229"),
            ("openai", "gpt-4-turbo"),
        ],
        Priority.MEDIUM: [
            ("openai", "gpt-4o-mini"),
            ("google", "gemini-1.5-pro"),
        ],
        Priority.LOW: [
            ("openai", "gpt-3.5-turbo"),
            ("anthropic", "claude-3-haiku-20240307"),
        ],
    }

    # Estimated costs per 1K output tokens (for routing decisions)
    ESTIMATED_COSTS = {
        ("openai", "gpt-4o"): 0.01,
        ("openai", "gpt-4o-mini"): 0.0006,
        ("openai", "gpt-4-turbo"): 0.03,
        ("openai", "gpt-4"): 0.06,
        ("openai", "gpt-3.5-turbo"): 0.002,
        ("anthropic", "claude-3-5-sonnet-20241022"): 0.015,
        ("anthropic", "claude-3-sonnet-20240229"): 0.015,
        ("anthropic", "claude-3-opus-20240229"): 0.075,
        ("anthropic", "claude-3-haiku-20240307"): 0.00125,
        ("google", "gemini-1.5-pro"): 0.005,
        ("google", "gemini-1.5-flash"): 0.0003,
        ("google", "gemini-pro"): 0.0015,
        ("xai", "grok-beta"): 0.015,
        ("xai", "grok-2"): 0.01,
    }

    def __init__(self, llm_gateway=None):
        """Initialize the cost router.

        Args:
            llm_gateway: Optional LLM Gateway instance for checking provider availability
        """
        self.llm_gateway = llm_gateway

    def select_model(
        self,
        priority: str = "medium",
        word_count: Optional[int] = None,
        max_budget_usd: Optional[float] = None,
    ) -> Tuple[str, str]:
        """Select the optimal model based on priority and constraints.

        Args:
            priority: Priority level ('high', 'medium', 'low')
            word_count: Target word count (affects token estimation)
            max_budget_usd: Maximum budget in USD

        Returns:
            Tuple of (provider_name, model_name)
        """
        selection = self.get_model_selection(priority, word_count, max_budget_usd)
        return (selection.provider, selection.model)

    def get_model_selection(
        self,
        priority: str = "medium",
        word_count: Optional[int] = None,
        max_budget_usd: Optional[float] = None,
    ) -> ModelSelection:
        """Get detailed model selection with reasoning.

        Args:
            priority: Priority level ('high', 'medium', 'low')
            word_count: Target word count (affects token estimation)
            max_budget_usd: Maximum budget in USD

        Returns:
            ModelSelection with provider, model, and reasoning
        """
        # Convert string priority to enum
        try:
            priority_enum = Priority(priority.lower())
        except ValueError:
            logger.warning(f"Invalid priority '{priority}', defaulting to MEDIUM")
            priority_enum = Priority.MEDIUM

        # Get default route for priority
        provider, model = self.DEFAULT_ROUTES[priority_enum]

        # Check if we need to respect budget constraints
        if max_budget_usd is not None and word_count is not None:
            # Estimate tokens needed (rough: 1.5 tokens per word)
            estimated_tokens = int(word_count * 1.5)
            estimated_cost = (estimated_tokens / 1000) * self.ESTIMATED_COSTS.get(
                (provider, model), 0.01
            )

            if estimated_cost > max_budget_usd:
                # Find a cheaper alternative
                cheaper_selection = self._find_cheaper_model(
                    priority_enum, estimated_tokens, max_budget_usd
                )
                if cheaper_selection:
                    return cheaper_selection

        # Check if provider is available (if gateway is configured)
        if self.llm_gateway:
            available = self.llm_gateway.get_available_providers()
            if provider not in available:
                # Try fallback routes
                for fallback_provider, fallback_model in self.FALLBACK_ROUTES.get(
                    priority_enum, []
                ):
                    if fallback_provider in available:
                        return ModelSelection(
                            provider=fallback_provider,
                            model=fallback_model,
                            estimated_cost_per_1k_tokens=self.ESTIMATED_COSTS.get(
                                (fallback_provider, fallback_model), 0.01
                            ),
                            reason=f"Fallback for {priority} priority (primary unavailable)",
                        )

        return ModelSelection(
            provider=provider,
            model=model,
            estimated_cost_per_1k_tokens=self.ESTIMATED_COSTS.get((provider, model), 0.01),
            reason=f"Default route for {priority} priority",
        )

    def _find_cheaper_model(
        self,
        priority: Priority,
        estimated_tokens: int,
        max_budget_usd: float,
    ) -> Optional[ModelSelection]:
        """Find a cheaper model that fits within budget.

        Args:
            priority: The original priority
            estimated_tokens: Estimated token usage
            max_budget_usd: Maximum budget

        Returns:
            ModelSelection if found, None otherwise
        """
        # Sort models by cost
        sorted_models = sorted(self.ESTIMATED_COSTS.items(), key=lambda x: x[1])

        for (provider, model), cost_per_1k in sorted_models:
            estimated_cost = (estimated_tokens / 1000) * cost_per_1k
            if estimated_cost <= max_budget_usd:
                return ModelSelection(
                    provider=provider,
                    model=model,
                    estimated_cost_per_1k_tokens=cost_per_1k,
                    reason=f"Budget-optimized selection (max: ${max_budget_usd})",
                )

        return None

    def estimate_cost(
        self,
        provider: str,
        model: str,
        word_count: int,
    ) -> float:
        """Estimate cost for generating content.

        Args:
            provider: Provider name
            model: Model name
            word_count: Target word count

        Returns:
            Estimated cost in USD
        """
        # Estimate tokens (input + output, roughly 3 tokens per word total)
        estimated_tokens = int(word_count * 3)
        cost_per_1k = self.ESTIMATED_COSTS.get((provider, model), 0.01)
        return (estimated_tokens / 1000) * cost_per_1k


# Global cost router instance
cost_router = CostRouter()
