"""NLP-based Intent Classifier for keywords."""

import logging
from typing import Dict, List, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Classifier for search intent using NLP models.

    Classifies keywords into one of four intent categories:
    - informational: User wants to learn something
    - commercial: User researching before purchase
    - navigational: User looking for specific site/page
    - transactional: User ready to take action/purchase
    """

    INTENT_CLASSES = ["informational", "commercial", "navigational", "transactional"]

    # Pattern-based rules for quick classification
    INTENT_PATTERNS = {
        "informational": [
            "how to", "what is", "what are", "why", "when", "who is",
            "where is", "which", "define", "meaning", "tutorial",
            "guide", "learn", "explain", "understand", "examples",
        ],
        "commercial": [
            "best", "top", "review", "reviews", "comparison", "compare",
            "vs", "versus", "alternative", "alternatives", "pros and cons",
            "cheap", "affordable", "premium", "quality",
        ],
        "navigational": [
            "login", "sign in", "sign up", "website", "site", "official",
            "homepage", "page", "account", "app", "download",
        ],
        "transactional": [
            "buy", "purchase", "order", "price", "pricing", "discount",
            "coupon", "deal", "deals", "sale", "shop", "store",
            "subscribe", "book", "reserve", "hire", "get",
        ],
    }

    def __init__(self, use_ml: bool = True):
        """Initialize the intent classifier.

        Args:
            use_ml: Whether to use ML model for classification.
                   Falls back to pattern matching if False or if ML fails.
        """
        self.use_ml = use_ml
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self._initialized = False

    def _init_model(self):
        """Lazily initialize the ML model."""
        if self._initialized:
            return

        if not self.use_ml:
            self._initialized = True
            return

        try:
            from transformers import pipeline

            # Use zero-shot classification for flexibility
            self._pipeline = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1,  # CPU
            )
            logger.info("Initialized zero-shot classification model")
            self._initialized = True
        except ImportError:
            logger.warning("transformers not installed, using pattern-based classification")
            self.use_ml = False
            self._initialized = True
        except Exception as e:
            logger.warning(f"Failed to initialize ML model: {e}, using pattern-based classification")
            self.use_ml = False
            self._initialized = True

    async def classify(self, keyword: str) -> Dict[str, float]:
        """Classify keyword intent and return probabilities.

        Args:
            keyword: The keyword to classify

        Returns:
            Dictionary mapping intent classes to probability scores (0-1)
        """
        self._init_model()

        keyword_lower = keyword.lower().strip()

        if not keyword_lower:
            return {intent: 0.25 for intent in self.INTENT_CLASSES}

        # Try ML classification first if available
        if self._pipeline is not None:
            try:
                result = self._pipeline(
                    keyword_lower,
                    candidate_labels=self.INTENT_CLASSES,
                    multi_label=False,
                )

                # Convert to dict with scores
                probs = {}
                for label, score in zip(result["labels"], result["scores"]):
                    probs[label] = round(score, 4)

                return probs
            except Exception as e:
                logger.warning(f"ML classification failed: {e}, using pattern matching")

        # Fall back to pattern-based classification
        return self._pattern_based_classify(keyword_lower)

    def _pattern_based_classify(self, keyword: str) -> Dict[str, float]:
        """Classify using pattern matching rules.

        Args:
            keyword: Lowercase keyword to classify

        Returns:
            Dictionary mapping intent classes to probability scores
        """
        scores = {intent: 0.0 for intent in self.INTENT_CLASSES}

        # Check each pattern category
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in keyword:
                    scores[intent] += 1.0

        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {k: round(v / total, 4) for k, v in scores.items()}
        else:
            # Default to informational if no patterns match
            scores["informational"] = 0.4
            scores["commercial"] = 0.2
            scores["navigational"] = 0.2
            scores["transactional"] = 0.2

        return scores

    async def get_primary_intent(self, keyword: str) -> str:
        """Get the primary intent class for a keyword.

        Args:
            keyword: The keyword to classify

        Returns:
            Primary intent class (highest probability)
        """
        probs = await self.classify(keyword)
        return max(probs, key=probs.get)

    async def get_intent_with_confidence(self, keyword: str) -> Dict[str, any]:
        """Get primary intent with confidence score.

        Args:
            keyword: The keyword to classify

        Returns:
            Dictionary with 'intent' and 'confidence' keys
        """
        probs = await self.classify(keyword)
        primary_intent = max(probs, key=probs.get)
        confidence = probs[primary_intent]

        return {
            "intent": primary_intent,
            "confidence": round(confidence * 100, 2),  # Convert to percentage
            "all_scores": probs,
        }

    async def classify_batch(
        self, keywords: List[str]
    ) -> List[Dict[str, any]]:
        """Classify multiple keywords in batch.

        Args:
            keywords: List of keywords to classify

        Returns:
            List of classification results
        """
        results = []
        for keyword in keywords:
            result = await self.get_intent_with_confidence(keyword)
            result["keyword"] = keyword
            results.append(result)
        return results


# Singleton instance for reuse
_intent_classifier: Optional[IntentClassifier] = None


def get_intent_classifier(use_ml: bool = True) -> IntentClassifier:
    """Get or create the intent classifier instance.

    Args:
        use_ml: Whether to use ML model

    Returns:
        IntentClassifier instance
    """
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier(use_ml=use_ml)
    return _intent_classifier
