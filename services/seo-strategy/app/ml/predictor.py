"""Ranking predictor using machine learning models."""

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class RankingPredictor:
    """ML-based ranking predictor for SEO keywords.

    Predicts the probability of a keyword ranking in the top 10
    search results based on various features like keyword difficulty,
    search volume, content quality score, etc.
    """

    # Default feature names expected by the model
    FEATURE_NAMES = [
        "keyword_difficulty",  # 0-100 score
        "search_volume",  # Monthly searches
        "competition",  # 0-1 competition level
        "content_word_count",  # Planned word count
        "domain_authority",  # 0-100 DA score
        "backlink_count",  # Number of backlinks
        "content_quality_score",  # 0-100 quality score
        "avg_competitor_word_count",  # Avg word count of top 10
        "avg_competitor_da",  # Avg DA of top 10
    ]

    def __init__(self, model_path: Optional[str] = None):
        """Initialize the ranking predictor.

        Args:
            model_path: Path to load a pre-trained model from
        """
        self._model = None
        self._is_trained = False
        self._feature_importance: Optional[Dict[str, float]] = None

        if model_path and Path(model_path).exists():
            self.load_model(model_path)

    def _init_model(self):
        """Initialize the ML model."""
        if self._model is not None:
            return

        try:
            from sklearn.ensemble import GradientBoostingClassifier

            self._model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
            )
            logger.info("Initialized GradientBoostingClassifier for ranking prediction")
        except ImportError:
            logger.warning("scikit-learn not available, using simple heuristics")

    def train(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Train the ranking prediction model.

        Args:
            features: Feature matrix of shape (n_samples, n_features)
            labels: Binary labels (1 = ranked in top 10, 0 = not)
            feature_names: Optional list of feature names

        Returns:
            Dictionary with training metrics
        """
        self._init_model()

        if self._model is None:
            logger.error("Model not initialized")
            return {"error": "Model not initialized"}

        try:
            from sklearn.model_selection import cross_val_score

            # Perform cross-validation
            cv_scores = cross_val_score(self._model, features, labels, cv=5)

            # Train on full data
            self._model.fit(features, labels)
            self._is_trained = True

            # Calculate feature importance
            if feature_names is None:
                feature_names = self.FEATURE_NAMES[: features.shape[1]]

            self._feature_importance = {}
            for name, importance in zip(
                feature_names, self._model.feature_importances_
            ):
                self._feature_importance[name] = float(importance)

            metrics = {
                "accuracy_mean": float(cv_scores.mean()),
                "accuracy_std": float(cv_scores.std()),
                "cv_scores": cv_scores.tolist(),
                "feature_importance": self._feature_importance,
            }

            logger.info(
                f"Model trained with CV accuracy: {metrics['accuracy_mean']:.2%}"
            )
            return metrics

        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {"error": str(e)}

    def predict_ranking_probability(
        self,
        features: np.ndarray,
    ) -> np.ndarray:
        """Predict probability of ranking in top 10.

        Args:
            features: Feature matrix of shape (n_samples, n_features)

        Returns:
            Array of probabilities (0-1) for ranking in top 10
        """
        if not self._is_trained:
            logger.warning("Model not trained, using heuristic prediction")
            return self._heuristic_predict(features)

        try:
            probabilities = self._model.predict_proba(features)[:, 1]
            return probabilities
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return self._heuristic_predict(features)

    def _heuristic_predict(self, features: np.ndarray) -> np.ndarray:
        """Simple heuristic-based prediction when model is not trained.

        Uses a weighted average of normalized features.

        Args:
            features: Feature matrix

        Returns:
            Array of probability estimates
        """
        # Feature weights (importance)
        weights = np.array([
            0.25,  # keyword_difficulty (negative - higher is harder)
            0.15,  # search_volume
            0.10,  # competition (negative)
            0.10,  # content_word_count
            0.15,  # domain_authority
            0.10,  # backlink_count
            0.10,  # content_quality_score
            0.03,  # avg_competitor_word_count (negative)
            0.02,  # avg_competitor_da (negative)
        ])

        # Pad or truncate weights to match feature count
        n_features = features.shape[1] if len(features.shape) > 1 else len(features)
        weights = weights[:n_features]
        if len(weights) < n_features:
            weights = np.pad(weights, (0, n_features - len(weights)))

        # Normalize features to 0-1 range (simple min-max per column)
        if len(features.shape) == 1:
            features = features.reshape(1, -1)

        # Simple scoring based on heuristics
        probabilities = []
        for row in features:
            score = 0.5  # Base probability

            # Keyword difficulty (lower is better)
            if len(row) > 0:
                kd = min(row[0] / 100, 1.0)
                score += (1 - kd) * 0.2

            # Search volume (higher is harder to rank, but more valuable)
            if len(row) > 1:
                sv = min(row[1] / 10000, 1.0)
                score -= sv * 0.05

            # Domain authority (higher is better)
            if len(row) > 4:
                da = min(row[4] / 100, 1.0)
                score += da * 0.15

            # Content quality (higher is better)
            if len(row) > 6:
                cq = min(row[6] / 100, 1.0)
                score += cq * 0.1

            probabilities.append(max(0, min(1, score)))

        return np.array(probabilities)

    def predict(
        self,
        features: np.ndarray,
        threshold: float = 0.5,
    ) -> np.ndarray:
        """Predict binary ranking outcome.

        Args:
            features: Feature matrix
            threshold: Probability threshold for positive class

        Returns:
            Binary predictions (1 = will rank, 0 = won't rank)
        """
        probabilities = self.predict_ranking_probability(features)
        return (probabilities >= threshold).astype(int)

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance scores.

        Returns:
            Dictionary mapping feature names to importance scores,
            or None if model not trained
        """
        return self._feature_importance

    def save_model(self, path: str) -> bool:
        """Save the trained model to disk.

        Args:
            path: Path to save the model

        Returns:
            True if successful, False otherwise
        """
        if not self._is_trained:
            logger.warning("Cannot save untrained model")
            return False

        try:
            model_data = {
                "model": self._model,
                "feature_importance": self._feature_importance,
                "is_trained": self._is_trained,
            }
            with open(path, "wb") as f:
                pickle.dump(model_data, f)
            logger.info(f"Model saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load_model(self, path: str) -> bool:
        """Load a trained model from disk.

        Args:
            path: Path to the saved model

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(path, "rb") as f:
                model_data = pickle.load(f)
            self._model = model_data["model"]
            self._feature_importance = model_data.get("feature_importance")
            self._is_trained = model_data.get("is_trained", True)
            logger.info(f"Model loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def create_features_from_dict(
        self,
        data: Dict[str, Any],
    ) -> np.ndarray:
        """Create feature array from dictionary of values.

        Args:
            data: Dictionary with feature values (uses FEATURE_NAMES as keys)

        Returns:
            Numpy array of features in the expected order
        """
        features = []
        for name in self.FEATURE_NAMES:
            value = data.get(name, 0)
            features.append(float(value) if value is not None else 0.0)
        return np.array(features)

    def predict_from_dict(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Predict ranking probability from a dictionary of features.

        Args:
            data: Dictionary with feature values

        Returns:
            Dictionary with prediction results
        """
        features = self.create_features_from_dict(data)
        probability = float(self.predict_ranking_probability(features.reshape(1, -1))[0])
        prediction = int(probability >= 0.5)

        return {
            "probability": round(probability, 4),
            "prediction": prediction,
            "will_rank": prediction == 1,
            "confidence": round(abs(probability - 0.5) * 2, 4),  # 0-1 confidence
        }


# Singleton instance
_ranking_predictor: Optional[RankingPredictor] = None


def get_ranking_predictor(model_path: Optional[str] = None) -> RankingPredictor:
    """Get or create the ranking predictor instance.

    Args:
        model_path: Optional path to load a pre-trained model

    Returns:
        RankingPredictor instance
    """
    global _ranking_predictor
    if _ranking_predictor is None:
        _ranking_predictor = RankingPredictor(model_path=model_path)
    return _ranking_predictor
