from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError
from slowapi.errors import RateLimitExceeded
from starlette.datastructures import MutableHeaders
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import Settings, get_settings
from app.limiter import limiter
from app.llm.cascade import LLMCascade
from app.llm.groq_provider import GroqProvider
from app.llm.openrouter_provider import OpenRouterProvider
from app.rag.embeddings import Embedder
from app.rag.index import build_index
from app.rag.retriever import EmptyRetriever, Retriever
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.session.store import SessionStore

logger = logging.getLogger("portfolio")

# Baseline headers on every HTTP response. Do not set Access-Control-* here —
# CORSMiddleware already owns those.
_SECURITY_HEADERS = (
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(raw=message.setdefault("headers", []))
                for name, value in _SECURITY_HEADERS:
                    headers[name] = value
            await send(message)

        await self.app(scope, receive, send_with_headers)


def _configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def _connect_redis(settings: Settings) -> Redis | None:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.ping()
        logger.info("redis connected")
        return client
    except (RedisError, OSError):
        logger.warning("redis unavailable at startup — sessions are stateless", exc_info=True)
        try:
            await client.aclose()
        except (RedisError, OSError):
            logger.debug("redis client close failed after ping error", exc_info=True)
        return None


def _build_cascade(settings: Settings) -> LLMCascade:
    return LLMCascade(
        [
            GroqProvider(settings.groq_api_key, settings.groq_model, settings.llm_timeout_seconds),
            OpenRouterProvider(
                settings.openrouter_api_key,
                settings.openrouter_model,
                settings.llm_timeout_seconds,
            ),
        ]
    )


def _rate_limit_reply(lang: str, settings: Settings) -> str:
    if lang == "ru":
        return "Слишком много сообщений. Подожди минуту и попробуй снова."
    return "Too many messages. Please wait a minute before sending another."


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    settings: Settings = getattr(request.app.state, "settings", get_settings())
    lang = "en"
    try:
        body: dict[str, Any] = await request.json()
        if body.get("lang") in {"en", "ru"}:
            lang = body["lang"]
    except ValueError:
        pass
    session_id = request.cookies.get(settings.cookie_name) or ""
    response = JSONResponse(
        status_code=429,
        content={
            "reply": _rate_limit_reply(lang, settings),
            "session_id": session_id,
            "source": "fallback_declined",
            "card": None,
            "attachments": None,
        },
        headers={"Retry-After": "60"},
    )
    return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    redis_client = await _connect_redis(settings)
    app.state.redis = redis_client
    app.state.session_store = SessionStore(redis_client, settings)

    if os.environ.get("SKIP_RAG") == "1":
        logger.info("SKIP_RAG=1 — using empty retriever")
        app.state.embedder = None
        app.state.retriever = EmptyRetriever()
    else:
        embedder = Embedder(model_name=settings.embedding_model)
        embedder.load()
        store = build_index(embedder)
        app.state.embedder = embedder
        app.state.retriever = Retriever(embedder, store)
    app.state.cascade = _build_cascade(settings)
    logger.info("startup complete")
    try:
        yield
    finally:
        if redis_client is not None:
            await redis_client.aclose()


def create_app() -> FastAPI:
    _configure_logging()
    settings = get_settings()
    app = FastAPI(title="NewGenSayomi API", lifespan=lifespan)
    app.state.settings = settings
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[arg-type]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    # Added last → outermost: runs after CORS so Access-Control-* stay intact.
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
