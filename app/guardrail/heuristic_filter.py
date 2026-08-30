from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import Settings
from app.guardrail.patterns import INJECTION_PATTERNS

_COMPILED = [re.compile(pattern, re.IGNORECASE | re.UNICODE) for pattern in INJECTION_PATTERNS]


@dataclass(frozen=True)
class FilterResult:
    declined: bool
    reply: str = ""


def declined_reply(lang: str, settings: Settings) -> str:
    if lang == "ru":
        return (
            f"Я могу отвечать только на вопросы о профессиональном опыте "
            f"{settings.developer_name_ru}."
        )
    return (
        f"I can only answer questions about {settings.developer_name_en}'s "
        "professional experience."
    )


def check_message(message: str, lang: str, settings: Settings) -> FilterResult:
    if len(message) > settings.max_message_chars:
        return FilterResult(declined=True, reply=declined_reply(lang, settings))
    for compiled in _COMPILED:
        if compiled.search(message):
            return FilterResult(declined=True, reply=declined_reply(lang, settings))
    return FilterResult(declined=False)
