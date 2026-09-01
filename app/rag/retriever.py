from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.rag.chunking import Chunk
from app.rag.embeddings import Embedder
from app.rag.index import FaissIndex

# Minimum inner-product similarity (higher = better match) for a topic-scoped
# search to be considered on-topic.  Renamed from "distance" to reflect
# that the FAISS IndexFlatIP returns raw cosine similarity on unit-normalized
# vectors — larger values mean closer match.
#
# ┌────────────────────────────────────────────────────────────────────────────
# │ IMPORTANT — lang=en DISCREPANCY
# │ The knowledge base (all .md files) is written entirely in RUSSIAN.
# │ all-MiniLM-L6-v2 is NOT a cross-lingual model.  When body.lang == "en",
# │ the raw English query is embedded directly against Russian chunks WITHOUT
# │ any translation step — this systematically degrades retrieval quality.
# │
# │ For lang=en, the off-topic gate is therefore DISABLED: is_off_topic()
# │ returns False regardless of scores.  The LLM cascade still receives the
# │ retrieved chunks (potentially poor quality) but the user never sees a
# │ misleading "I only answer about X" canned redirect for a legitimate
# │ English question.
# │
# │ To properly support lang=en, add a translation layer before retrieval:
# │   - Option A (simpler): translate EN query → RU before encode()
# │   - Option B (better): replace all-MiniLM-L6-v2 with a cross-lingual
# │     model such as multilingual-e5-base or paraphrase-multilingual-MiniLM
# │ After either fix, re-run scripts/calibrate_threshold.py and re-enable
# │ the off-topic gate for lang=en.
# └────────────────────────────────────────────────────────────────────────────
#
# Calibration on all-MiniLM-L6-v2 (384d) + this corpus + RUSSIAN queries
# (matching the KB language), with topic-first (filter-before-rank) search:
#   relevant   scores:  min=0.054  max=0.667  avg=0.351
#   irrelevant scores:  min=0.107  max=0.641  avg=0.328
#   best separating threshold ≈ 0.15  →  ~62% accuracy
#
# Note: accuracy ceiling is low due to corpus size (16 chunks, 5 topics) and
# all-MiniLM-L6-v2's limited discriminability at 384 dimensions.
MAX_TOPIC_DISTANCE = 0.15

# The set of topic-scoped knowledge files. ``faq.md`` is intentionally absent —
# it is a cross-cutting FAQ that is always searched regardless of topic.
TOPIC_FILES: dict[str, str] = {
    "me": "me.md",
    "projects": "projects.md",
    "skills": "skills.md",
    "fun": "fun.md",
    "contact": "contact.md",
}


class EmptyRetriever:
    """Used in unit tests that skip loading MiniLM."""

    def retrieve(self, query: str, k: int = 4) -> list[Chunk]:
        return []

    def retrieve_scored(
        self, query: str, topic: str | None = None, top_k: int = 4
    ) -> list["RetrievedChunk"]:
        return []


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


class Retriever:
    def __init__(self, embedder: Embedder, store: FaissIndex) -> None:
        self._embedder = embedder
        self._store = store

    def retrieve(self, query: str, k: int = 4) -> list[Chunk]:
        """Backward-compatible shim — returns chunks without scores."""
        return [
            retrieved.chunk
            for retrieved in self.retrieve_scored(query, topic=None, top_k=k)
        ]

    def retrieve_scored(
        self, query: str, topic: str | None = None, top_k: int = 4
    ) -> list[RetrievedChunk]:
        """Return ranked chunks with their FAISS IP scores.

        Two search modes:

        topic is None — full-corpus search:
            Encode query, run FAISS top-k, return results as-is.
            This is the right strategy for 16-chunk corpus where the
            full index fits in CPU cache.

        topic is set — topic-scoped search:
            1. Filter candidate chunks by source file first.
            2. Encode query.
            3. Score ONLY those filtered chunks (no top-k pre-filter that
               could discard relevant chunks of the target topic).
            4. Sort by score ascending (L2: lower = better).
            5. Return top_k of the scoped results.

        This ensures no chunk is lost due to competition from chunks of
        other topics in the global top-k ranking.
        """
        if not query.strip() or self._store.index.ntotal == 0:
            return []
        vector = self._embedder.encode([query])

        wanted_source = TOPIC_FILES.get(topic) if topic else None

        if wanted_source is None:
            # Full-corpus search: use FAISS top-k (fast, no pre-filter needed).
            k = min(top_k, self._store.index.ntotal)
            scores, ids = self._store.index.search(
                np.ascontiguousarray(vector), k
            )
            results: list[RetrievedChunk] = []
            for idx, score in zip(ids[0], scores[0]):
                if idx < 0:
                    continue
                results.append(
                    RetrievedChunk(chunk=self._store.chunks[int(idx)], score=float(score))
                )
            return results

        # Topic-scoped: filter chunks by source BEFORE ranking.
        # This prevents relevant chunks from being pre-filtered by the global
        # top-k which could discard them if other topics dominate the scores.
        topic_indices: list[int] = [
            i for i, chunk in enumerate(self._store.chunks)
            if chunk.source == wanted_source
        ]
        if not topic_indices:
            return []

        # Score only the topic-filtered chunks against the query.
        topic_vectors = self._store.vectors[topic_indices]  # (N_topic, dim)
        # FAISS IndexFlatIP: np.dot(q, d) on unit vectors = IP similarity
        # (higher = better match on L2-normalized embeddings).
        topic_scores = np.dot(topic_vectors, vector[0]).astype(np.float32)
        # Sort descending (best IP match first).
        order = np.argsort(topic_scores)[::-1]
        results = []
        for rank, vec_idx in enumerate(order[:top_k]):
            chunk_idx = topic_indices[vec_idx]
            results.append(
                RetrievedChunk(
                    chunk=self._store.chunks[chunk_idx],
                    score=float(topic_scores[vec_idx]),
                )
            )
        return results


def is_off_topic(
    topic: str | None,
    results: list[RetrievedChunk],
    lang: str = "ru",
    max_distance: float = MAX_TOPIC_DISTANCE,
) -> bool:
    """True when a topic-scoped search returned nothing meaningfully related.

    The retriever computes raw FAISS IndexFlatIP (inner product) between the
    query vector and chunk vectors.  On L2-normalized embeddings from
    all-MiniLM-L6-v2, higher IP = closer match (cosine similarity).

    A question is off-topic when even the best-matching chunk scores too
    low — i.e. max(score) falls below max_distance (the minimum acceptable
    similarity for the topic to be considered relevant).

    Off-topic detection is DISABLED for lang=en because the knowledge base is
    entirely in Russian and all-MiniLM-L6-v2 is not cross-lingual — English
    queries systematically produce poor embeddings against Russian chunks,
    making score-based gating unreliable.  See MAX_TOPIC_DISTANCE docstring for
    details and the recommended fix (translation layer or cross-lingual model).

    - No topic set → never off-topic (full-base search covers everything).
    - lang="en" → never off-topic (EN embeddings are unreliable for RU KB).
    - No results → off-topic.
    - Best chunk score below max_distance → off-topic.
    """
    if topic is None:
        return False
    # Disable off-topic gate for English — see MAX_TOPIC_DISTANCE docstring.
    if lang == "en":
        return False
    if not results:
        return True
    # IP similarity: higher score = better match (closer in embedding space).
    # A chunk is acceptably similar when its score >= threshold.
    # Therefore: off-topic when max(score) < threshold.
    return max(result.score for result in results) < max_distance