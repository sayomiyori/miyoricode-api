from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any, Literal

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.guardrail.heuristic_filter import check_message
from app.guardrail.output_filter import filter_output
from app.guardrail.system_prompt import (
    build_system_prompt,
    llm_unavailable_fallback,
    wrap_user_question,
)
from app.limiter import limiter
from app.llm.cascade import LLMCascade
from app.llm.base import LLMError
from app.rag.retriever import Retriever
from app.session.store import SessionStore
from app.tools.structured_answers import (
    match_attachments,
    match_project_carousel,
    match_structured,
)

logger = logging.getLogger("portfolio.routes")

router = APIRouter()
settings_for_limits = get_settings()

# Hard ceiling for an obviously anomalous JSON body. Product length (1500) still
# lives in heuristic_filter so the chat UX stays HTTP 200 + fallback_declined.
MAX_MESSAGE_PAYLOAD_CHARS = 5000

# Heartbeat / keep-alive is not emitted by default — Groq streams fast enough
# that idle gaps are short. If a long pause ever appears between events,
# introduce `: ping\n\n` comments on a background task here.
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_PAYLOAD_CHARS)
    lang: Literal["en", "ru"]
    session_id: str | None = None


class AttachmentImage(BaseModel):
    url: str
    frame: Literal["phone", "browser"]
    alt: str


class ChatAttachments(BaseModel):
    link: str | None = None
    images: list[AttachmentImage] | None = None


class CarouselLink(BaseModel):
    label: str
    url: str


class CarouselItem(BaseModel):
    id: str
    title: str
    category: str
    year: str
    cover_image: str | None = None
    cover_gradient: list[str] | None = None
    description: str
    technologies: list[str]
    link: str | None = None
    links: list[CarouselLink] = []
    screenshots: list[AttachmentImage] = []


class ChatCard(BaseModel):
    type: Literal["project_carousel"]
    items: list[CarouselItem]


# Response model kept for OpenAPI / legacy callers; the actual wire format is SSE.
class ChatResponse(BaseModel):
    reply: str
    session_id: str
    source: Literal["structured", "rag", "fallback_declined"]
    card: ChatCard | None = None
    attachments: ChatAttachments | None = None


def _format_sse(event: str, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def attach_session_cookie(response: Response, session_id: str, settings: Settings) -> None:
    samesite = settings.cookie_samesite.lower()
    if samesite not in {"lax", "strict", "none"}:
        samesite = "lax"
    response.set_cookie(
        key=settings.cookie_name,
        value=session_id,
        httponly=True,
        samesite=samesite,  # type: ignore[arg-type]
        secure=settings.cookie_secure,
        max_age=settings.session_ttl_seconds,
        path="/",
    )


def _canonical_session_uuid(value: str | None) -> str | None:
    """Accept only UUID4. Arbitrary strings must not become Redis keys."""
    if not value:
        return None
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        return None
    if parsed.version != 4:
        return None
    return str(parsed)


def _resolve_session_id(body: ChatRequest, request: Request, settings: Settings) -> str:
    for candidate in (body.session_id, request.cookies.get(settings.cookie_name)):
        canonical = _canonical_session_uuid(candidate)
        if canonical is not None:
            return canonical
    return str(uuid.uuid4())


def _build_sse_response(
    generator: AsyncIterator[bytes],
    cookie_response: Response,
) -> StreamingResponse:
    """Build a StreamingResponse and copy Set-Cookie headers from cookie_response.

    FastAPI's StreamingResponse accepts arbitrary headers but does not support
    set_cookie() directly — use a normal Response to compute cookie headers
    first, then merge them in.
    """
    headers = {**dict(cookie_response.headers), **SSE_HEADERS}
    return StreamingResponse(generator, media_type="text/event-stream", headers=headers)


@router.post("/chat")
@limiter.limit(f"{settings_for_limits.rate_limit_per_minute}/minute")
@limiter.limit(f"{settings_for_limits.rate_limit_per_day}/day")
async def chat(request: Request, body: ChatRequest) -> StreamingResponse:
    settings: Settings = request.app.state.settings
    session_id = _resolve_session_id(body, request, settings)

    # Set-Cookie has to be computed on a real Response object.
    cookie_response = Response()
    attach_session_cookie(cookie_response, session_id, settings)

    # 1) Input guardrail — blocking, before any SSE bytes.
    filtered = check_message(body.message, body.lang, settings)
    if filtered.declined:
        async def _declined_stream() -> AsyncIterator[bytes]:
            yield _format_sse(
                "metadata",
                {
                    "card": None,
                    "attachments": None,
                    "session_id": session_id,
                    "source": "fallback_declined",
                },
            )
            yield _format_sse(
                "token",
                {"text": filtered.reply},
            )
            yield _format_sse(
                "done",
                {"source": "fallback_declined", "session_id": session_id},
            )
        return _build_sse_response(_declined_stream(), cookie_response)

    # 2) Resolve path + overlays (sync, fast, deterministic).
    store: SessionStore = request.app.state.session_store
    history = await store.get_history(session_id)

    structured = match_structured(body.message)
    if structured is not None:
        context = structured.content
        source: Literal["structured", "rag"] = "structured"
        knowledge_prefix = (
            "Structured source document — translate in full. "
            "Copy every URL and proper name character-for-character:\n"
        )
    else:
        retriever: Retriever = request.app.state.retriever
        chunks = retriever.retrieve(body.message, k=settings.retrieve_k)
        context = "\n\n".join(
            f"source={chunk.source} heading={chunk.heading}\n{chunk.text}" for chunk in chunks
        )
        source = "rag"
        knowledge_prefix = "Retrieved knowledge:\n"

    messages: list[dict[str, str]] = [
        {"role": "system", "content": build_system_prompt(body.lang, settings, source=source)},
        {
            "role": "system",
            "content": knowledge_prefix + (context or "(empty)"),
        },
    ]
    for item in history:
        messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": wrap_user_question(body.message)})

    # 3) Pre-compute overlays — depend only on (message, lang), NOT on LLM output.
    attachments = match_attachments(body.message)
    card = (
        None
        if attachments is not None
        else match_project_carousel(body.message, body.lang)
    )

    cascade: LLMCascade = request.app.state.cascade
    fallback_text = llm_unavailable_fallback(body.lang, settings)

    async def event_stream() -> AsyncIterator[bytes]:
        # [a] metadata FIRST — overlay + session + source. Card/attachments
        # are independent of the LLM, so the client can render them before
        # any tokens arrive.
        yield _format_sse(
            "metadata",
            {
                "card": card,
                "attachments": attachments,
                "session_id": session_id,
                "source": source,
            },
        )

        # [b] stream tokens from the cascade. We buffer the full reply so the
        # output leak filter can scan it on the complete text (canary patterns
        # are substring-based and require the whole message).
        reply_buf: list[str] = []
        try:
            async for chunk in cascade.stream(messages, fallback=fallback_text):
                reply_buf.append(chunk)
                yield _format_sse("token", {"text": chunk})
        except (httpx.HTTPError, LLMError) as exc:
            logger.warning("stream interrupted: %s", exc)
            yield _format_sse(
                "error",
                {"reason": "stream_failed", "detail": str(exc) or type(exc).__name__},
            )
            return

        # [c] finalize — output filter, persist, done.
        full_reply = "".join(reply_buf)
        filtered_reply, leaked = filter_output(
            full_reply,
            body.lang,
            settings,
            enforce_length=(source == "rag"),
        )
        if leaked:
            yield _format_sse(
                "done",
                {
                    "source": "fallback_declined",
                    "session_id": session_id,
                    "reason": "output_filter",
                },
            )
            return
        try:
            await store.append_turn(session_id, body.message, filtered_reply)
        except Exception:
            logger.exception("session persist failed")
        yield _format_sse(
            "done",
            {"source": source, "session_id": session_id},
        )

    return _build_sse_response(event_stream(), cookie_response)
