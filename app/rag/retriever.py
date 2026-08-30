from __future__ import annotations

import numpy as np

from app.rag.chunking import Chunk
from app.rag.embeddings import Embedder
from app.rag.index import FaissIndex


class EmptyRetriever:
    """Used in unit tests that skip loading MiniLM."""

    def retrieve(self, query: str, k: int = 4) -> list[Chunk]:
        return []


class Retriever:
    def __init__(self, embedder: Embedder, store: FaissIndex) -> None:
        self._embedder = embedder
        self._store = store

    def retrieve(self, query: str, k: int = 4) -> list[Chunk]:
        if not query.strip() or self._store.index.ntotal == 0:
            return []
        k = min(k, self._store.index.ntotal)
        vector = self._embedder.encode([query])
        _scores, ids = self._store.index.search(np.ascontiguousarray(vector), k)
        results: list[Chunk] = []
        for idx in ids[0]:
            if idx < 0:
                continue
            results.append(self._store.chunks[int(idx)])
        return results
