import httpx
import pytest

from app.llm.base import LLMError, LLMProvider
from app.llm.cascade import LLMCascade


class FakeProvider(LLMProvider):
    def __init__(self, name: str, *, configured: bool = True, error: Exception | None = None, text: str = "ok"):
        self.name = name
        self._configured = configured
        self._error = error
        self._text = text
        self.calls = 0

    def is_configured(self) -> bool:
        return self._configured

    async def generate(self, messages: list[dict[str, str]]) -> str:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._text


@pytest.mark.asyncio
async def test_cascade_skips_missing_key():
    groq = FakeProvider("groq", configured=False)
    openrouter = FakeProvider("openrouter", text="from-openrouter")
    cascade = LLMCascade([groq, openrouter])
    result = await cascade.generate([{"role": "user", "content": "hi"}], fallback="fb")
    assert result == "from-openrouter"
    assert groq.calls == 0
    assert openrouter.calls == 1


@pytest.mark.asyncio
async def test_cascade_falls_through_on_401():
    groq = FakeProvider("groq", error=LLMError("http_401", status_code=401))
    openrouter = FakeProvider("openrouter", text="from-openrouter")
    cascade = LLMCascade([groq, openrouter])
    result = await cascade.generate([{"role": "user", "content": "hi"}], fallback="fb")
    assert result == "from-openrouter"
    assert groq.calls == 1
    assert openrouter.calls == 1


@pytest.mark.asyncio
async def test_cascade_falls_through_on_timeout():
    groq = FakeProvider("groq", error=LLMError("timeout"))
    openrouter = FakeProvider("openrouter", text="from-openrouter")
    cascade = LLMCascade([groq, openrouter])
    result = await cascade.generate([{"role": "user", "content": "hi"}], fallback="fb")
    assert result == "from-openrouter"


@pytest.mark.asyncio
async def test_cascade_fallback_when_both_fail():
    groq = FakeProvider("groq", error=LLMError("http_500", status_code=500))
    openrouter = FakeProvider("openrouter", error=httpx.TimeoutException("t"))
    cascade = LLMCascade([groq, openrouter])
    result = await cascade.generate([{"role": "user", "content": "hi"}], fallback="contact-me")
    assert result == "contact-me"
    assert groq.calls == 1
    assert openrouter.calls == 1


@pytest.mark.asyncio
async def test_cascade_does_not_raise_to_caller():
    groq = FakeProvider("groq", error=LLMError("http_403", status_code=403))
    openrouter = FakeProvider("openrouter", error=LLMError("http_429", status_code=429))
    cascade = LLMCascade([groq, openrouter])
    result = await cascade.generate([], fallback="safe")
    assert result == "safe"
