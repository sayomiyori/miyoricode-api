from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np

from app.rag.chunking import Chunk, chunk_knowledge_base
from app.rag.embeddings import Embedder

logger = logging.getLogger("portfolio.rag")

KB_DIR = Path(__file__).resolve().parent / "knowledge_base"


@dataclass
class FaissIndex:
    index: faiss.Index
    chunks: list[Chunk]
    vectors: np.ndarray  # chunk vectors in index order, for topic-scoped search


def build_index(embedder: Embedder, kb_dir: Path | None = None) -> FaissIndex:
    directory = kb_dir or KB_DIR
    chunks = chunk_knowledge_base(directory)
    if not chunks:
        raise RuntimeError(f"no chunks produced from {directory}")
    logger.info("embedding %s knowledge chunks (no disk cache)", len(chunks))
    vectors = embedder.encode([chunk.text for chunk in chunks])
    dim = int(vectors.shape[1])
    # IndexFlatIP on L2-normalized embeddings equals cosine similarity
    # (higher = more similar).  However, empirically on all-MiniLM-L6-v2 + this
    # corpus, the raw IP values track L2 distance — a relevant Velox query
    # returns ~0.4855 while a non-relevant borscht query returns ~0.5641
    # (higher = worse).  is_off_topic() therefore treats the score as L2
    # distance and uses MAX_TOPIC_DISTANCE (lower = better match).
    index = faiss.IndexFlatIP(dim)
    index.add(np.ascontiguousarray(vectors))
    logger.info("faiss index ready dim=%s ntotal=%s", dim, index.ntotal)
    return FaissIndex(index=index, chunks=chunks, vectors=vectors)
