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


def test_topic_scoped_search_does_not_return_other_topics(retriever: Retriever):
    """retrieve_scored with topic='projects' must never return chunks from skills.md."""
    hits = retriever.retrieve_scored("Python async SQLAlchemy", topic="projects", top_k=8)
    assert hits
    assert all(hit.chunk.source == "projects.md" for hit in hits)


def test_topic_scoped_search_returns_scored_results(retriever: Retriever):
    hits = retriever.retrieve_scored("AI platform runners", topic="projects", top_k=4)
    assert hits
    for hit in hits:
        assert hasattr(hit, "score")
        # Scores are FAISS IndexFlatIP on L2-normalized MiniLM vectors.
        # Range is roughly [-1, 1] in theory but on real embeddings with this
        # corpus we see [-0.1, 0.4] — just check it is a finite float.
        assert isinstance(hit.score, float) and -1.0 <= hit.score <= 1.0


def test_is_off_topic_returns_true_for_no_results(retriever: Retriever):
    from app.rag.retriever import is_off_topic, RetrievedChunk
    assert is_off_topic("projects", []) is True


def test_is_off_topic_returns_true_when_best_score_too_high(retriever: Retriever):
    """L2 distance: lower score = better match.  Score > MAX_TOPIC_DISTANCE → off-topic."""
    from app.rag.retriever import is_off_topic, RetrievedChunk, MAX_TOPIC_DISTANCE
    from app.rag.chunking import Chunk
    # Score above the RU-calibrated threshold (0.49) — distant match.
    far = RetrievedChunk(chunk=Chunk(text="foo", source="projects.md", heading=""), score=0.60)
    assert is_off_topic("projects", [far], lang="ru") is True


def test_is_off_topic_returns_false_when_score_within_threshold(retriever: Retriever):
    """L2 distance: lower score = better match.  Score ≤ MAX_TOPIC_DISTANCE → on-topic."""
    from app.rag.retriever import is_off_topic, RetrievedChunk
    from app.rag.chunking import Chunk
    # Score well within the RU-calibrated threshold — close enough to be on-topic.
    close = RetrievedChunk(chunk=Chunk(text="Velox AI platform", source="projects.md", heading="Velox"), score=0.20)
    assert is_off_topic("projects", [close], lang="ru") is False


def test_is_off_topic_disabled_for_english(retriever: Retriever):
    """Off-topic gate is disabled for lang=en because the RU KB + EN query is unreliable."""
    from app.rag.retriever import is_off_topic, RetrievedChunk
    from app.rag.chunking import Chunk
    # Same far chunk that would be off-topic for RU — but EN always passes.
    far = RetrievedChunk(chunk=Chunk(text="foo", source="projects.md", heading=""), score=0.99)
    assert is_off_topic("projects", [far], lang="en") is False
    # Also with an empty result list.
    assert is_off_topic("projects", [], lang="en") is False


def test_is_off_topic_never_true_when_topic_is_none(retriever: Retriever):
    from app.rag.retriever import is_off_topic
    assert is_off_topic(None, []) is False
