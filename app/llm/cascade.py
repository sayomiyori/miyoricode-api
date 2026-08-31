from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import httpx

from app.llm.base import LLMError, LLMProvider

logger = logging.getLogger("portfolio.llm")

# Invalid key (401/403) must fall through — otherwise a bad Groq key never reaches OpenRouter.
RETRYABLE_STATUS = {401, 403, 408, 429, 500, 502, 503, 504}


class LLMCascade:
    def __init__(self, providers: list[LLMProvider]) -> None:
        self._providers = providers

    async def generate(self, messages: list[dict[str, str]], fallback: str) -> str:
        attempt = 0
        for provider in self._providers:
            attempt += 1
            if not provider.is_configured():
                logger.info(
                    "llm_skip provider=%s attempt=%s reason=missing_api_key",
                    provider.name,
                    attempt,
                )
                continue
            try:
                text = await provider.generate(messages)
                logger.info(
                    "llm_ok provider=%s attempt=%s",
                    provider.name,
                    attempt,
                )
                return text
            except LLMError as exc:
                if exc.status_code is not None and exc.status_code not in RETRYABLE_STATUS:
                    logger.warning(
                        "llm_fail provider=%s attempt=%s reason=%s status=%s (trying next)",
                        provider.name,
                        attempt,
                        exc.reason,
                        exc.status_code,
                    )
                else:
                    logger.warning(
                        "llm_fail provider=%s attempt=%s reason=%s status=%s",
                        provider.name,
                        attempt,
                        exc.reason,
                        exc.status_code,
                    )
            except httpx.TimeoutException:
                logger.warning(
                    "llm_fail provider=%s attempt=%s reason=timeout",
                    provider.name,
                    attempt,
                )
            except httpx.HTTPError:
                logger.warning(
                    "llm_fail provider=%s attempt=%s reason=http_error",
                    provider.name,
                    attempt,
                    extra={},
                )
                logger.warning("llm connection error", exc_info=True)

        logger.warning("llm_fallback after %s attempts — both providers unavailable", attempt)
        return fallback

    async def stream(self, messages: list[dict[str, str]], fallback: str) -> AsyncIterator[str]:
        """Stream tokens from the first provider that succeeds.

        Switching providers mid-stream would discard already-emitted tokens, so
        a failure after the first yield terminates the cascade. Falls back to
        yielding the full fallback string only when every provider failed
        before producing anything.
        """
        attempt = 0
        last_error: Exception | None = None
        for provider in self._providers:
            attempt += 1
            if not provider.is_configured():
                logger.info(
                    "llm_skip provider=%s attempt=%s reason=missing_api_key",
                    provider.name,
                    attempt,
                )
                continue
            try:
                emitted = False
                async for chunk in provider.stream_generate(messages):
                    emitted = True
                    yield chunk
                logger.info(
                    "llm_ok provider=%s attempt=%s (stream)",
                    provider.name,
                    attempt,
                )
                return
            except LLMError as exc:
                last_error = exc
                if emitted:
                    logger.warning(
                        "llm_stream_broken provider=%s attempt=%s reason=%s status=%s",
                        provider.name,
                        attempt,
                        exc.reason,
                        exc.status_code,
                    )
                    return
                logger.warning(
                    "llm_fail provider=%s attempt=%s reason=%s status=%s (trying next)",
                    provider.name,
                    attempt,
                    exc.reason,
                    exc.status_code,
                )
            except httpx.TimeoutException:
                last_error = httpx.TimeoutException("timeout")
                if emitted:
                    logger.warning(
                        "llm_stream_broken provider=%s attempt=%s reason=timeout",
                        provider.name,
                        attempt,
                    )
                    return
                logger.warning(
                    "llm_fail provider=%s attempt=%s reason=timeout",
                    provider.name,
                    attempt,
                )
            except httpx.HTTPError as exc:
                last_error = exc
                if emitted:
                    logger.warning(
                        "llm_stream_broken provider=%s attempt=%s reason=http_error",
                        provider.name,
                        attempt,
                    )
                    logger.warning("llm connection error mid-stream", exc_info=True)
                    return
                logger.warning(
                    "llm_fail provider=%s attempt=%s reason=http_error",
                    provider.name,
                    attempt,
                )
                logger.warning("llm connection error", exc_info=True)

        logger.warning(
            "llm_fallback after %s attempts — both providers unavailable (stream)",
            attempt,
        )
        if last_error is not None:
            logger.info("stream_fallback_reason=%s", type(last_error).__name__)
        yield fallback
