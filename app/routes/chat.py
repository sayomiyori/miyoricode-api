from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Request, Response
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
from app.rag.retriever import Retriever
from app.session.store import SessionStore
from app.tools.structured_answers import match_structured

router = APIRouter()
settings_for_limits = get_settings()

# Hard ceiling for an obviously anomalous JSON body. Product length (1500) still
# lives in heuristic_filter so the chat UX stays HTTP 200 + fallback_declined.
MAX_MESSAGE_PAYLOAD_CHARS = 5000


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_PAYLOAD_CHARS)
    lang: Literal["en", "ru"]
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    source: Literal["structured", "rag", "fallback_declined"]


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


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{settings_for_limits.rate_limit_per_minute}/minute")
@limiter.limit(f"{settings_for_limits.rate_limit_per_day}/day")
async def chat(request: Request, body: ChatRequest, response: Response) -> ChatResponse:
    settings: Settings = request.app.state.settings
    session_id = _resolve_session_id(body, request, settings)
    attach_session_cookie(response, session_id, settings)

    filtered = check_message(body.message, body.lang, settings)
    if filtered.declined:
        return ChatResponse(
            reply=filtered.reply,
            session_id=session_id,
            source="fallback_declined",
        )

    store: SessionStore = request.app.state.session_store
    history = await store.get_history(session_id)

    structured = match_structured(body.message)
    if structured is not None:
        context = structured.content
        source: Literal["structured", "rag", "fallback_declined"] = "structured"
    else:
        retriever: Retriever = request.app.state.retriever
        chunks = retriever.retrieve(body.message, k=settings.retrieve_k)
        context = "\n\n".join(
            f"source={chunk.source} heading={chunk.heading}\n{chunk.text}" for chunk in chunks
        )
        source = "rag"

    messages: list[dict[str, str]] = [
        {"role": "system", "content": build_system_prompt(body.lang, settings)},
        {
            "role": "system",
            "content": "Retrieved knowledge (may be PLACEHOLDER fixtures):\n" + (context or "(empty)"),
        },
    ]
    for item in history:
        messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": wrap_user_question(body.message)})

    cascade: LLMCascade = request.app.state.cascade
    raw = await cascade.generate(messages, fallback=llm_unavailable_fallback(body.lang, settings))
    reply, leaked = filter_output(raw, body.lang, settings)
    if leaked:
        return ChatResponse(
            reply=reply,
            session_id=session_id,
            source="fallback_declined",
        )

    await store.append_turn(session_id, body.message, reply)
    return ChatResponse(reply=reply, session_id=session_id, source=source)
