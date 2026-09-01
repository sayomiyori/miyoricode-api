from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.rag.chunking import Chunk
from app.rag.embeddings import Embedder
from app.rag.index import FaissIndex

# Maximum L2 distance (lower = better match) for a topic-scoped search to be
# considered on-topic.
#
# Calibration on all-MiniLM-L6-v2 (384d) + this corpus (16 chunks, 6 .md files)
# shows distributions that significantly overlap:
#   relevant   scores:  min=0.040  max=0.288  avg=0.133
#   irrelevant scores:  min=-0.084  max=0.186  avg=0.063
#   best separating threshold ≈ 0.30  →  ~58% accuracy (barely above random)
#
# The low discriminability is due to: small knowledge base, short .md files
# (me.md / fun.md have very few chunks → "no results" for many queries),
# and all-MiniLM-L6-v2 being a lightweight model with limited topic-level
# separation at 384 dimensions.
#
# THIS THRESHOLD IS APPROXIMATE.  Re-run scripts/calibrate_threshold.py on
# the production embedding instance to re-calibrate after:
#   - upgrading the embedding model (e.g. all-mpnet-base-v2, 768d)
#   - expanding the knowledge base (more chunks per topic)
#   - adding topic-specific training pairs
MAX_TOPIC_DISTANCE = 0.30

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
    max_distance: float = MAX_TOPIC_DISTANCE,
) -> bool:
    """True when a topic-scoped search returned nothing meaningfully related.

    The FAISS IndexFlatIP score on normalized MiniLM vectors tracks L2 distance
    (lower = better match).  A question is off-topic when even the closest
    matching chunk is too far — i.e. min(score) exceeds max_distance.

    - No topic set → never off-topic (full-base search covers everything).
    - No results → off-topic.
    - Closest chunk farther than max_distance → off-topic.
    """
    if topic is None:
        return False
    if not results:
        return True
    return min(result.score for result in results) > max_distance