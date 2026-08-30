from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("portfolio.embeddings")


@dataclass
class Embedder:
    model_name: str
    _model: SentenceTransformer | None = None

    def load(self) -> None:
        logger.info("loading embedding model %s", self.model_name)
        self._model = SentenceTransformer(self.model_name)
        logger.info("embedding model ready")

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            raise RuntimeError("Embedder.load() was not called")
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)
