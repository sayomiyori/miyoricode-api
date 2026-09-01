from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.rag.chunking import Chunk
from app.rag.embeddings import Embedder
from app.rag.index import FaissIndex

# Maximum L2 distance (lower = better match) for a topic-scoped search to be
# considered on-topic.
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
# (matching the KB language):
#   relevant   scores:  min=0.187  max=0.494  avg=0.298
#   irrelevant scores:  min=0.226  max=0.374  avg=0.291
#   best separating threshold ≈ 0.49  →  ~68% accuracy
#
# Key observations from RU calibration:
#   - projects.md: rich chunks, best discrimination
#   - skills.md:  decent separation
#   - me.md / fun.md: almost no chunks → "no results" for most queries
#   - contact.md:  few chunks, moderate overlap with irrelevant
#
# With only 16 total chunks the ceiling is low.  Expand the knowledge base
# before trusting this threshold for high-stakes routing decisions.
MAX_TOPIC_DISTANCE = 0.49

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
        """Return ranked chunks with their cosine similarity scores.

        If ``topic`` is set, only chunks from the matching source file are
        considered. With 16 chunks total, post-search filtering is cheaper
        than a separate index per topic — no premature optimization.
        """
        if not query.strip() or self._store.index.ntotal == 0:
            return []
        top_k = min(top_k, self._store.index.ntotal)
        vector = self._embedder.encode([query])
        scores, ids = self._store.index.search(np.ascontiguousarray(vector), top_k)
        wanted_source = TOPIC_FILES.get(topic) if topic else None
        results: list[RetrievedChunk] = []
        for idx, score in zip(ids[0], scores[0]):
            if idx < 0:
                continue
            chunk = self._store.chunks[int(idx)]
            if wanted_source is not None and chunk.source != wanted_source:
                continue
            results.append(RetrievedChunk(chunk=chunk, score=float(score)))
        return results


def is_off_topic(
    topic: str | None,
    results: list[RetrievedChunk],
    lang: str = "ru",
    max_distance: float = MAX_TOPIC_DISTANCE,
) -> bool:
    """True when a topic-scoped search returned nothing meaningfully related.

    The FAISS IndexFlatIP score on normalized MiniLM vectors tracks L2 distance
    (lower = better match).  A question is off-topic when even the closest
    matching chunk is too far — i.e. min(score) exceeds max_distance.

    Off-topic detection is DISABLED for lang=en because the knowledge base is
    entirely in Russian and all-MiniLM-L6-v2 is not cross-lingual — English
    queries systematically produce poor embeddings against Russian chunks,
    making score-based gating unreliable.  See MAX_TOPIC_DISTANCE docstring for
    details and the recommended fix (translation layer or cross-lingual model).

    - No topic set → never off-topic (full-base search covers everything).
    - lang="en" → never off-topic (EN embeddings are unreliable for RU KB).
    - No results → off-topic.
    - Closest chunk farther than max_distance → off-topic.
    """
    if topic is None:
        return False
    # Disable off-topic gate for English — see MAX_TOPIC_DISTANCE docstring.
    if lang == "en":
        return False
    if not results:
        return True
    return min(result.score for result in results) > max_distance