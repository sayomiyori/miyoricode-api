import pytest
from redis.exceptions import RedisError

from app.config import Settings
from app.session.schema import ChatMessage
from app.session.store import SessionStore


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.expires: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.data[key] = value
        if ex is not None:
            self.expires[key] = ex

    async def ping(self) -> bool:
        return True


class BrokenRedis:
    async def get(self, key: str) -> str | None:
        raise RedisError("down")

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        raise RedisError("down")

    async def ping(self) -> bool:
        raise RedisError("down")


@pytest.mark.asyncio
async def test_append_and_read_history_trimmed_to_six():
    settings = Settings(session_history_limit=6, session_ttl_seconds=1800)
    redis = FakeRedis()
    store = SessionStore(redis, settings)  # type: ignore[arg-type]
    for i in range(5):
        await store.append_turn("abc", f"u{i}", f"a{i}")
    history = await store.get_history("abc")
    assert len(history) == 6
    assert history[0] == ChatMessage(role="user", content="u2")
    assert redis.expires["session:abc"] == 1800


@pytest.mark.asyncio
async def test_missing_redis_returns_empty_and_does_not_raise():
    settings = Settings()
    store = SessionStore(None, settings)
    assert await store.get_history("x") == []
    await store.append_turn("x", "u", "a")
    assert await store.ping() is False


@pytest.mark.asyncio
async def test_redis_errors_degrade_gracefully():
    settings = Settings()
    store = SessionStore(BrokenRedis(), settings)  # type: ignore[arg-type]
    assert await store.get_history("x") == []
    await store.append_turn("x", "u", "a")
    assert await store.ping() is False
