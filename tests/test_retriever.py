from pathlib import Path

import pytest

from app.rag.chunking import chunk_knowledge_base
from app.rag.embeddings import Embedder
from app.rag.index import build_index
from app.rag.retriever import Retriever

KB = Path(__file__).resolve().parents[1] / "app" / "rag" / "knowledge_base"


@pytest.fixture(scope="module")
def retriever() -> Retriever:
    embedder = Embedder(model_name="all-MiniLM-L6-v2")
    embedder.load()
    store = build_index(embedder, kb_dir=KB)
    return Retriever(embedder, store)


def test_knowledge_files_are_chunked():
    chunks = chunk_knowledge_base(KB)
    sources = {chunk.source for chunk in chunks}
    assert "projects.md" in sources
    assert "me.md" in sources
    assert chunks


def test_retrieve_projects_query_hits_projects_file(retriever: Retriever):
    hits = retriever.retrieve("расскажи о проектах", k=4)
    assert hits
    assert any(chunk.source == "projects.md" for chunk in hits)


def test_retrieve_english_projects_query(retriever: Retriever):
    hits = retriever.retrieve("Tell me about your projects", k=4)
    assert any(chunk.source == "projects.md" for chunk in hits)
