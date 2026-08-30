from __future__ import annotations

import json
import logging
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import Settings
from app.session.schema import ChatMessage

logger = logging.getLogger("portfolio.session")


class SessionStore:
    def __init__(self, client: Redis | None, settings: Settings) -> None:
        self._client = client
        self._ttl = settings.session_ttl_seconds
        self._limit = settings.session_history_limit

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def get_history(self, session_id: str) -> list[ChatMessage]:
        if self._client is None:
            return []
        try:
            raw = await self._client.get(self._key(session_id))
        except RedisError:
            logger.warning("redis unavailable: reading session as empty", exc_info=True)
            return []
        if not raw:
            return []
        try:
            payload: list[dict[str, Any]] = json.loads(raw)
            return [ChatMessage.model_validate(item) for item in payload]
        except (json.JSONDecodeError, ValueError):
            logger.warning("corrupt session payload for %s — resetting", session_id)
            return []

    async def append_turn(self, session_id: str, user_text: str, assistant_text: str) -> None:
        if self._client is None:
            return
        history = await self.get_history(session_id)
        history.append(ChatMessage(role="user", content=user_text))
        history.append(ChatMessage(role="assistant", content=assistant_text))
        trimmed = history[-self._limit :]
        payload = json.dumps([item.model_dump() for item in trimmed], ensure_ascii=False)
        try:
            await self._client.set(self._key(session_id), payload, ex=self._ttl)
        except RedisError:
            logger.warning("redis unavailable: session not persisted", exc_info=True)

    async def ping(self) -> bool:
        if self._client is None:
            return False
        try:
            return bool(await self._client.ping())
        except RedisError:
            return False
