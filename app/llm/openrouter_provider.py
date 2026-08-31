import json
from collections.abc import AsyncIterator

import httpx

from app.llm.base import LLMError, LLMProvider


class OpenRouterProvider(LLMProvider):
    name = "openrouter"
    _url = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, model: str, timeout: float) -> None:
        self._api_key = api_key.strip()
        self._model = model
        self._timeout = timeout

    def is_configured(self) -> bool:
        return bool(self._api_key)

    @staticmethod
    def _headers(api_key: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "NewGenSayomi Portfolio Chat",
        }

    @staticmethod
    def _payload(model: str, messages: list[dict[str, str]], stream: bool) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 2000,
        }
        if stream:
            payload["stream"] = True
        return payload

    async def generate(self, messages: list[dict[str, str]]) -> str:
        headers = self._headers(self._api_key)
        payload = self._payload(self._model, messages, stream=False)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMError("timeout", status_code=None) from exc
        except httpx.HTTPError as exc:
            raise LLMError("http_error", status_code=None) from exc

        if response.status_code >= 400:
            raise LLMError(f"http_{response.status_code}", status_code=response.status_code)

        data = response.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("malformed_response", status_code=response.status_code) from exc
        if not isinstance(text, str) or not text.strip():
            raise LLMError("empty_response", status_code=response.status_code)
        return text.strip()

    async def stream_generate(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        headers = self._headers(self._api_key)
        payload = self._payload(self._model, messages, stream=True)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", self._url, headers=headers, json=payload) as response:
                    if response.status_code >= 400:
                        await response.aread()
                        raise LLMError(
                            f"http_{response.status_code}",
                            status_code=response.status_code,
                        )
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if not line.startswith("data:"):
                            continue
                        data_str = line[len("data:"):].strip()
                        if not data_str or data_str == "[DONE]":
                            if data_str == "[DONE]":
                                return
                            continue
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError as exc:
                            raise LLMError("malformed_stream_chunk", status_code=None) from exc
                        try:
                            delta = chunk["choices"][0]["delta"]
                        except (KeyError, IndexError, TypeError) as exc:
                            raise LLMError("malformed_stream_chunk", status_code=None) from exc
                        piece = delta.get("content")
                        if isinstance(piece, str) and piece:
                            yield piece
        except httpx.TimeoutException as exc:
            raise LLMError("timeout", status_code=None) from exc
        except httpx.HTTPError as exc:
            raise LLMError("http_error", status_code=None) from exc
