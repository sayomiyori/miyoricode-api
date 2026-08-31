from __future__ import annotations

import os
import uuid

os.environ.setdefault("SKIP_RAG", "1")
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("OPENROUTER_API_KEY", "")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")

from collections.abc import AsyncIterator, Generator

import pytest
from fastapi.testclient import TestClient
from starlette.responses import Response

from app.config import get_settings
from app.limiter import limiter
from app.main import app
from app.routes.chat import MAX_MESSAGE_PAYLOAD_CHARS, _canonical_session_uuid
from app.session.store import SessionStore
from tests.test_session import FakeRedis


class FakeCascade:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    def _resolve_text(self, messages: list[dict[str, str]]) -> str:
        blob = " ".join(item["content"] for item in messages)
        if "Respond only in English" in blob or "только на русском" in blob:
            lang_ok = True
        else:
            lang_ok = False
        if ("меня зовут Х" in blob or "меня зовут X" in blob) and "как меня зовут" in blob.lower():
            return "Тебя зовут Х"
        if not lang_ok:
            return "missing-lang-instruction"
        for item in messages:
            if item["role"] == "system" and "только на русском" in item["content"]:
                return "Это ответ на русском про placeholder-проекты."
        return "This is an English placeholder reply about projects."

    async def generate(self, messages: list[dict[str, str]], fallback: str) -> str:
        self.calls.append(messages)
        return self._resolve_text(messages)

    async def stream(
        self, messages: list[dict[str, str]], fallback: str
    ) -> AsyncIterator[str]:
        self.calls.append(messages)
        text = self._resolve_text(messages)
        # Emit word-by-word (with trailing space) to mimic real token chunks.
        for index, word in enumerate(text.split(" ")):
            chunk = word if index == 0 else " " + word
            yield chunk


@pytest.fixture()
def cascade() -> FakeCascade:
    return FakeCascade()


@pytest.fixture()
def client(cascade: FakeCascade) -> Generator[TestClient, None, None]:
    get_settings.cache_clear()
    limiter.reset()
    with TestClient(app) as test_client:
        test_client.app.state.cascade = cascade
        test_client.app.state.session_store = SessionStore(FakeRedis(), get_settings())  # type: ignore[arg-type]
        yield test_client
