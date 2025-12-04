"""Keyword clustering using TF-IDF, K-Means, and semantic embeddings."""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class KeywordClusterer:
    """Cluster keywords using TF-IDF/K-Means or semantic embeddings.

    Supports two clustering approaches:
    1. TF-IDF + K-Means: Fast, works well for keyword text similarity
    2. Semantic (SBERT): Better semantic understanding, uses embeddings
    """

    def __init__(self, use_semantic: bool = True):
        """Initialize the keyword clusterer.

        Args:
            use_semantic: Whether to enable semantic clustering (requires sentence-transformers)
        """
        self.use_semantic = use_semantic
        self._sbert_model = None
        self._sbert_initialized = False

    def _init_sbert(self):
        """Lazily initialize SBERT model for semantic clustering."""
        if self._sbert_initialized:
            return

        if not self.use_semantic:
            self._sbert_initialized = True
            return

        try:
            from sentence_transformers import SentenceTransformer

            self._sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Initialized SBERT model for semantic clustering")
            self._sbert_initialized = True
        except ImportError:
            logger.warning(
                "sentence-transformers not installed, semantic clustering unavailable"
            )
            self.use_semantic = False
            self._sbert_initialized = True
        except Exception as e:
            logger.warning(f"Failed to initialize SBERT model: {e}")
            self.use_semantic = False
            self._sbert_initialized = True

    def cluster_tfidf(
        self,
        keywords: List[str],
        n_clusters: int = 5,
        random_state: int = 42,
    ) -> Dict[str, any]:
        """Cluster keywords using TF-IDF vectorization and K-Means.

        Args:
            keywords: List of keywords to cluster
            n_clusters: Number of clusters to create
            random_state: Random seed for reproducibility

        Returns:
            Dictionary containing:
                - labels: Cluster labels for each keyword
                - clusters: Dict mapping cluster_id to list of keywords
                - centroids: Cluster centroid feature names
        """
        if not keywords:
            return {"labels": [], "clusters": {}, "centroids": []}

        # Adjust n_clusters if we have fewer keywords
        n_clusters = min(n_clusters, len(keywords))
        if n_clusters < 2:
            return {
                "labels": [0] * len(keywords),
                "clusters": {0: keywords},
                "centroids": [],
            }

        try:
            from sklearn.cluster import KMeans
            from sklearn.feature_extraction.text import TfidfVectorizer

            # Vectorize keywords
            vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
                max_features=1000,
            )
            X = vectorizer.fit_transform(keywords)

            # Cluster using K-Means
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=random_state,
                n_init=10,
            )
            labels = kmeans.fit_predict(X)

            # Organize keywords by cluster
            clusters: Dict[int, List[str]] = {}
            for idx, label in enumerate(labels):
                label_int = int(label)
                if label_int not in clusters:
                    clusters[label_int] = []
                clusters[label_int].append(keywords[idx])

            # Get top features for each centroid
            feature_names = vectorizer.get_feature_names_out()
            centroids = []
            for centroid in kmeans.cluster_centers_:
                top_indices = centroid.argsort()[-5:][::-1]
                top_features = [feature_names[i] for i in top_indices]
                centroids.append(top_features)

            return {
                "labels": labels.tolist(),
                "clusters": clusters,
                "centroids": centroids,
            }
        except ImportError:
            logger.error("scikit-learn is required for TF-IDF clustering")
            raise RuntimeError("scikit-learn is required for TF-IDF clustering")

    def cluster_semantic(
        self,
        keywords: List[str],
        threshold: float = 0.3,
        min_samples: int = 2,
    ) -> Dict[str, any]:
        """Cluster keywords using SBERT embeddings and DBSCAN.

        Uses sentence-transformers to generate embeddings, then DBSCAN
        for density-based clustering that doesn't require a fixed number
        of clusters.

        Args:
            keywords: List of keywords to cluster
            threshold: Distance threshold for DBSCAN (eps parameter).
                      Lower values create more, tighter clusters.
            min_samples: Minimum samples to form a cluster

        Returns:
            Dictionary containing:
                - labels: Cluster labels (-1 indicates noise/outlier)
                - clusters: Dict mapping cluster_id to list of keywords
                - n_clusters: Number of clusters found
                - n_noise: Number of noise points
        """
        if not keywords:
            return {"labels": [], "clusters": {}, "n_clusters": 0, "n_noise": 0}

        self._init_sbert()

        if self._sbert_model is None:
            logger.warning("SBERT not available, falling back to TF-IDF clustering")
            result = self.cluster_tfidf(keywords)
            result["n_clusters"] = len(result["clusters"])
            result["n_noise"] = 0
            return result

        try:
            from sklearn.cluster import DBSCAN

            # Generate embeddings
            embeddings = self._sbert_model.encode(keywords, show_progress_bar=False)

            # Cluster using DBSCAN with cosine distance
            clustering = DBSCAN(
                eps=threshold,
                min_samples=min_samples,
                metric="cosine",
            )
            labels = clustering.fit_predict(embeddings)

            # Organize keywords by cluster
            clusters: Dict[int, List[str]] = {}
            noise_count = 0
            for idx, label in enumerate(labels):
                label_int = int(label)
                if label_int == -1:
                    noise_count += 1
                if label_int not in clusters:
                    clusters[label_int] = []
                clusters[label_int].append(keywords[idx])

            # Count real clusters (excluding noise label -1)
            n_clusters = len([k for k in clusters.keys() if k != -1])

            return {
                "labels": labels.tolist(),
                "clusters": clusters,
                "n_clusters": n_clusters,
                "n_noise": noise_count,
            }
        except ImportError:
            logger.error("scikit-learn is required for DBSCAN clustering")
            raise RuntimeError("scikit-learn is required for semantic clustering")

    def get_embeddings(self, keywords: List[str]) -> Optional[np.ndarray]:
        """Get SBERT embeddings for keywords.

        Args:
            keywords: List of keywords to embed

        Returns:
            Numpy array of embeddings, or None if SBERT unavailable
        """
        if not keywords:
            return None

        self._init_sbert()

        if self._sbert_model is None:
            return None

        return self._sbert_model.encode(keywords, show_progress_bar=False)

    def compute_similarity(
        self,
        keyword1: str,
        keyword2: str,
    ) -> Optional[float]:
        """Compute semantic similarity between two keywords.

        Args:
            keyword1: First keyword
            keyword2: Second keyword

        Returns:
            Cosine similarity score (0-1), or None if SBERT unavailable
        """
        self._init_sbert()

        if self._sbert_model is None:
            return None

        embeddings = self._sbert_model.encode(
            [keyword1, keyword2],
            show_progress_bar=False,
        )

        # Compute cosine similarity
        from numpy.linalg import norm

        similarity = np.dot(embeddings[0], embeddings[1]) / (
            norm(embeddings[0]) * norm(embeddings[1])
        )
        return float(similarity)

    def find_similar_keywords(
        self,
        query: str,
        keywords: List[str],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """Find keywords most similar to a query.

        Args:
            query: Query keyword
            keywords: List of keywords to search
            top_k: Number of results to return
            threshold: Minimum similarity score

        Returns:
            List of (keyword, similarity_score) tuples, sorted by similarity
        """
        if not keywords:
            return []

        self._init_sbert()

        if self._sbert_model is None:
            logger.warning("SBERT not available for similarity search")
            return []

        # Encode query and keywords
        query_embedding = self._sbert_model.encode([query], show_progress_bar=False)[0]
        keyword_embeddings = self._sbert_model.encode(keywords, show_progress_bar=False)

        # Compute similarities
        from numpy.linalg import norm

        similarities = []
        for i, kw_emb in enumerate(keyword_embeddings):
            sim = float(
                np.dot(query_embedding, kw_emb)
                / (norm(query_embedding) * norm(kw_emb))
            )
            if sim >= threshold:
                similarities.append((keywords[i], sim))

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


# Singleton instance
_keyword_clusterer: Optional[KeywordClusterer] = None


def get_keyword_clusterer(use_semantic: bool = True) -> KeywordClusterer:
    """Get or create the keyword clusterer instance.

    Args:
        use_semantic: Whether to enable semantic clustering

    Returns:
        KeywordClusterer instance
    """
    global _keyword_clusterer
    if _keyword_clusterer is None:
        _keyword_clusterer = KeywordClusterer(use_semantic=use_semantic)
    return _keyword_clusterer
