import httpx

from app.llm.base import LLMError, LLMProvider


class GroqProvider(LLMProvider):
    name = "groq"
    _url = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str, model: str, timeout: float) -> None:
        self._api_key = api_key.strip()
        self._model = model
        self._timeout = timeout

    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def generate(self, messages: list[dict[str, str]]) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 2000,
        }
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
