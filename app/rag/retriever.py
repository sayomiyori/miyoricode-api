from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.rag.chunking import Chunk
from app.rag.embeddings import Embedder
from app.rag.index import FaissIndex

# Conservative starting threshold — to be calibrated against real traffic.
# Cosine similarity (IndexFlatIP on normalized MiniLM vectors) maps roughly to
# the fraction of embedding mass aligned with the query; <0.35 usually means
# the knowledge base has no relevant chunk for the asked topic.
MIN_TOPIC_SIMILARITY = 0.35

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
    threshold: float = MIN_TOPIC_SIMILARITY,
) -> bool:
    """True when a topic-scoped search returned nothing meaningfully related.

    - No topic set → never off-topic (full-base search is expected to cover anything).
    - No results at all → off-topic.
    - Best score below threshold → off-topic.
    """
    if topic is None:
        return False
    if not results:
        return True
    best = max(result.score for result in results)
    return best < threshold