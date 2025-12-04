"""Adaptive Scorer for self-learning weight adjustment.

This module provides functionality to learn optimal weights
based on article performance data.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from app.services.auto_scorer import AutoScorer

logger = logging.getLogger(__name__)


class AdaptiveScorer:
    """Adaptive scorer that learns optimal weights from performance data."""

    # Minimum samples required for training
    MIN_SAMPLES_FOR_TRAINING = 10

    # Feature names in order (must match analysis keys)
    FEATURE_NAMES = [
        "title_contains_keyword",
        "h1_present",
        "h1_contains_keyword",
        "h2_contains_keyword",
        "keyword_density_ok",
        "images_have_alt",
        "word_count_adequate",
        "has_internal_links",
        "has_external_links",
        "meta_description",
    ]

    def __init__(self):
        """Initialize the adaptive scorer."""
        self.model: Optional[LogisticRegression] = None
        self.scaler: Optional[StandardScaler] = None
        self.learned_weights: Optional[Dict[str, int]] = None

    def _extract_features(self, checklist_values: Dict[str, Any]) -> List[float]:
        """Extract features from checklist values.

        Args:
            checklist_values: Dictionary of SEO checklist values.

        Returns:
            List of feature values as floats.
        """
        features = []
        for feature_name in self.FEATURE_NAMES:
            value = checklist_values.get(feature_name, False)
            # Convert to float (True -> 1.0, False -> 0.0)
            features.append(1.0 if value else 0.0)
        return features

    def train(
        self,
        articles_data: List[Dict[str, Any]],
        ranking_threshold: int = 10,
    ) -> Dict[str, Any]:
        """Train the model to learn optimal weights.

        Args:
            articles_data: List of articles with SEO checklist and performance data.
                Each article should have:
                - seo_checklist_values: Dict of SEO factor values
                - avg_position: Average search position (lower is better)
            ranking_threshold: Position threshold for "good" ranking.

        Returns:
            Dictionary with training results.
        """
        if len(articles_data) < self.MIN_SAMPLES_FOR_TRAINING:
            logger.warning(
                f"Not enough samples for training: {len(articles_data)} "
                f"(minimum: {self.MIN_SAMPLES_FOR_TRAINING})"
            )
            return {
                "success": False,
                "reason": "insufficient_data",
                "samples": len(articles_data),
                "required": self.MIN_SAMPLES_FOR_TRAINING,
            }

        # Prepare training data
        X = []
        y = []

        for article in articles_data:
            checklist = article.get("seo_checklist_values", {})
            avg_position = article.get("avg_position")

            if checklist and avg_position is not None:
                features = self._extract_features(checklist)
                X.append(features)
                # Good ranking = True (position < threshold)
                y.append(1 if avg_position < ranking_threshold else 0)

        if len(X) < self.MIN_SAMPLES_FOR_TRAINING:
            return {
                "success": False,
                "reason": "insufficient_valid_data",
                "valid_samples": len(X),
                "required": self.MIN_SAMPLES_FOR_TRAINING,
            }

        X_array = np.array(X)
        y_array = np.array(y)

        # Check if we have both classes
        unique_classes = np.unique(y_array)
        if len(unique_classes) < 2:
            logger.warning("Training data has only one class, cannot train model")
            return {
                "success": False,
                "reason": "single_class_data",
                "class_distribution": {str(c): int((y_array == c).sum()) for c in unique_classes},
            }

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_array)

        # Train logistic regression model
        self.model = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
        )
        self.model.fit(X_scaled, y_array)

        # Extract learned weights from coefficients
        self.learned_weights = self._coefficients_to_weights(self.model.coef_[0])

        logger.info(f"Model trained with {len(X)} samples")
        logger.info(f"Learned weights: {self.learned_weights}")

        return {
            "success": True,
            "samples_used": len(X),
            "learned_weights": self.learned_weights,
            "model_accuracy": self._calculate_accuracy(X_scaled, y_array),
            "class_distribution": {
                "good_rankings": int((y_array == 1).sum()),
                "poor_rankings": int((y_array == 0).sum()),
            },
        }

    def _coefficients_to_weights(self, coefficients: np.ndarray) -> Dict[str, int]:
        """Convert model coefficients to scoring weights.

        Args:
            coefficients: Model coefficients array.

        Returns:
            Dictionary of feature weights.
        """
        # Normalize coefficients to positive values
        # Use absolute values and scale to sum to 100
        abs_coef = np.abs(coefficients)
        total = abs_coef.sum()

        if total == 0:
            # Fall back to equal weights
            equal_weight = 100 // len(self.FEATURE_NAMES)
            return {name: equal_weight for name in self.FEATURE_NAMES}

        weights = {}
        for i, name in enumerate(self.FEATURE_NAMES):
            # Scale to 0-25 range per feature, ensure minimum of 1
            weight = max(1, int((abs_coef[i] / total) * 100))
            weights[name] = weight

        return weights

    def _calculate_accuracy(
        self, X_scaled: np.ndarray, y: np.ndarray
    ) -> float:
        """Calculate model accuracy on training data.

        Args:
            X_scaled: Scaled feature matrix.
            y: Target labels.

        Returns:
            Accuracy as float.
        """
        if self.model is None:
            return 0.0
        return float(self.model.score(X_scaled, y))

    async def adjust_weights(
        self,
        workspace_id: UUID,
        get_articles_func,
        update_weights_func,
    ) -> Dict[str, Any]:
        """Adjust weights for a workspace based on article performance.

        Args:
            workspace_id: The workspace ID.
            get_articles_func: Async function to get articles with performance data.
            update_weights_func: Async function to update workspace weights.

        Returns:
            Dictionary with adjustment results.
        """
        try:
            # Get articles with performance data
            articles = await get_articles_func(workspace_id)

            if not articles:
                return {
                    "success": False,
                    "reason": "no_articles",
                    "workspace_id": str(workspace_id),
                }

            # Train model
            training_result = self.train(articles)

            if not training_result.get("success"):
                return {
                    **training_result,
                    "workspace_id": str(workspace_id),
                }

            # Update weights in database
            new_weights = training_result.get("learned_weights", {})
            await update_weights_func(workspace_id, new_weights)

            logger.info(
                f"Updated weights for workspace {workspace_id}: {new_weights}"
            )

            return {
                "success": True,
                "workspace_id": str(workspace_id),
                "new_weights": new_weights,
                "training_details": training_result,
            }

        except Exception as e:
            logger.error(f"Failed to adjust weights for workspace {workspace_id}: {e}")
            return {
                "success": False,
                "reason": "error",
                "error": str(e),
                "workspace_id": str(workspace_id),
            }

    def get_scorer_with_learned_weights(self) -> AutoScorer:
        """Get an AutoScorer configured with learned weights.

        Returns:
            AutoScorer instance with learned weights.
        """
        if self.learned_weights:
            return AutoScorer(weights=self.learned_weights)
        return AutoScorer()

    def predict_ranking_probability(
        self, checklist_values: Dict[str, Any]
    ) -> Optional[float]:
        """Predict probability of good ranking for given checklist values.

        Args:
            checklist_values: SEO checklist values.

        Returns:
            Probability of good ranking (0-1) or None if model not trained.
        """
        if self.model is None or self.scaler is None:
            return None

        features = self._extract_features(checklist_values)
        features_scaled = self.scaler.transform([features])
        probability = self.model.predict_proba(features_scaled)[0][1]
        return float(probability)
