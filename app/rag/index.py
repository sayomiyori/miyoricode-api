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


def build_index(embedder: Embedder, kb_dir: Path | None = None) -> FaissIndex:
    directory = kb_dir or KB_DIR
    chunks = chunk_knowledge_base(directory)
    if not chunks:
        raise RuntimeError(f"no chunks produced from {directory}")
    logger.info("embedding %s knowledge chunks (no disk cache)", len(chunks))
    vectors = embedder.encode([chunk.text for chunk in chunks])
    dim = int(vectors.shape[1])
    index = faiss.IndexFlatIP(dim)
    index.add(np.ascontiguousarray(vectors))
    logger.info("faiss index ready dim=%s ntotal=%s", dim, index.ntotal)
    return FaissIndex(index=index, chunks=chunks)
