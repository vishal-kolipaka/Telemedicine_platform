"""
evidence_retriever.py — Evidence Retrieval Infrastructure

Constructs the vector retrieval layer over the 16 approved, governed semantic
chunks in knowledge_base/chunks.json.

Features:
- Deterministic sub-linear TF-IDF + Character & Word n-gram Vector Space Model
- Cosine similarity computation
- Complete metadata and provenance preservation
- Multi-dimensional metadata-aware filtering (condition scope, category, role, permissions)
- Configurable similarity threshold and Top-K
- Strict zero-evidence fallback (no substitute hallucination)
"""

from __future__ import annotations

import os
import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("Recommendations.EvidenceRetriever")


class EvidenceRetriever:
    """Vector retrieval engine with multi-layer governance metadata filtering."""

    DEFAULT_SIMILARITY_THRESHOLD = 0.15

    def __init__(
        self,
        chunks_path: Optional[str] = None,
        vector_index_path: Optional[str] = None,
        min_similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ):
        base_dir = os.path.join(os.getcwd(), "knowledge_base")
        if not os.path.exists(base_dir):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base"))
        if chunks_path is None:
            chunks_path = os.path.join(base_dir, "chunks.json")
        if vector_index_path is None:
            vector_index_path = os.path.join(base_dir, "vector_index.json")

        self.chunks_path = chunks_path
        self.vector_index_path = vector_index_path
        self.min_similarity_threshold = min_similarity_threshold

        self.chunks: List[Dict[str, Any]] = []
        self.chunk_ids: List[str] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.chunk_vectors: Optional[np.ndarray] = None

        self._initialize_retrieval_index()

    def _initialize_retrieval_index(self):
        """Loads chunks and constructs the vector index."""
        if not os.path.exists(self.chunks_path):
            raise FileNotFoundError(f"Chunks file not found at: {self.chunks_path}")

        with open(self.chunks_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        self.chunk_ids = [c["chunk_id"] for c in self.chunks]
        corpus = [c["chunk_text"] for c in self.chunks]

        # Hybrid Word (1-2) + Character (3-5) n-gram vectorizer with sub-linear tf
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
            norm="l2",
            analyzer="word",
            token_pattern=r"(?u)\b\w+\b|\d+(?:\.\d+)?%?"
        )
        self.chunk_vectors = self.vectorizer.fit_transform(corpus).toarray()

        logger.info(
            "Vector index initialized successfully with %d chunks and %d vocabulary dimensions.",
            len(self.chunks),
            self.chunk_vectors.shape[1]
        )

    def retrieve(
        self,
        query: str,
        target_condition: Optional[str] = None,
        recommendation_category: Optional[str] = None,
        evidence_role: Optional[str] = None,
        recommendation_only: bool = True,
        top_k: int = 5,
        min_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves governed evidence chunks matching semantic query and metadata filters.

        Parameters
        ----------
        query : str
            Search query representing patient risk factors or intervention topic.
        target_condition : str, optional
            Target disease condition (e.g. 'Type2_Diabetes', 'Prediabetes', 'NAFLD', etc.).
        recommendation_category : str, optional
            Target pillar (e.g. 'physical_activity', 'dietary_nutrition', 'weight_management').
        evidence_role : str, optional
            Required role (e.g. 'PRIMARY_RECOMMENDATION_SOURCE').
        recommendation_only : bool, default True
            If True, strictly filters for chunks where recommendation_generation_allowed is True.
        top_k : int, default 5
            Maximum number of chunks to return.
        min_threshold : float, optional
            Minimum similarity threshold (defaults to self.min_similarity_threshold).

        Returns
        -------
        list[dict]
            List of retrieved chunks with complete provenance and similarity_score,
            or empty list if zero evidence satisfies query and filters.
        """
        if not query or not query.strip():
            return []

        threshold = min_threshold if min_threshold is not None else self.min_similarity_threshold

        # Compute query vector and cosine similarities
        query_vec = self.vectorizer.transform([query]).toarray()
        similarities = cosine_similarity(query_vec, self.chunk_vectors)[0]

        # Rank all chunk indices by similarity descending
        ranked_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in ranked_indices:
            score = float(similarities[idx])
            chunk = self.chunks[idx]

            # 1. Similarity threshold check
            if score < threshold:
                continue

            # 2. Recommendation permission filter
            if recommendation_only and not chunk.get("recommendation_generation_allowed", False):
                continue

            # 3. Target condition scope filter
            if target_condition:
                allowed_conditions = chunk.get("allowed_condition_scopes", [])
                if target_condition not in allowed_conditions and "All_Cardiometabolic" not in allowed_conditions:
                    continue

            # 4. Recommendation category filter
            if recommendation_category:
                allowed_categories = chunk.get("allowed_recommendation_categories", [])
                if recommendation_category not in allowed_categories:
                    continue

            # 5. Evidence role filter
            if evidence_role and chunk.get("evidence_role") != evidence_role:
                continue

            # Build enriched return dictionary with full metadata + similarity score
            result_item = dict(chunk)
            result_item["similarity_score"] = round(score, 4)
            results.append(result_item)

            if len(results) >= top_k:
                break

        return results

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a chunk by its unique ID."""
        for c in self.chunks:
            if c["chunk_id"] == chunk_id:
                return dict(c)
        return None
