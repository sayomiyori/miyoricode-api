from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent.parent / "rag" / "knowledge_base"

CATEGORY_FILES = {
    "me": "me.md",
    "projects": "projects.md",
    "skills": "skills.md",
    "fun": "fun.md",
    "contact": "contact.md",
}

# Shortcut button labels and common paraphrases. No separate request flag from the frontend.
TRIGGERS: list[tuple[str, str]] = [
    ("me", "me"),
    ("about you", "me"),
    ("about yourself", "me"),
    ("who are you", "me"),
    ("tell me about yourself", "me"),
    ("tell me about you", "me"),
    ("кто ты", "me"),
    ("расскажи о себе", "me"),
    ("о себе", "me"),
    ("projects", "projects"),
    ("your projects", "projects"),
    ("tell me about your projects", "projects"),
    ("расскажи о проектах", "projects"),
    ("про проекты", "projects"),
    ("проекты", "projects"),
    ("skills", "skills"),
    ("your skills", "skills"),
    ("tell me about your skills", "skills"),
    ("навыки", "skills"),
    ("скиллы", "skills"),
    ("расскажи о навыках", "skills"),
    ("fun", "fun"),
    ("fun facts", "fun"),
    ("something fun", "fun"),
    ("пошути", "fun"),
    ("для души", "fun"),
    ("contact", "contact"),
    ("how to contact", "contact"),
    ("how can i reach you", "contact"),
    ("связаться", "contact"),
    ("контакты", "contact"),
]


@dataclass(frozen=True)
class StructuredMatch:
    category: str
    content: str
    source_file: str


def match_structured(message: str) -> StructuredMatch | None:
    normalized = " ".join(message.strip().lower().split())
    if not normalized:
        return None
    for phrase, category in TRIGGERS:
        if normalized == phrase or normalized == phrase + "?" or normalized == phrase + "!":
            filename = CATEGORY_FILES[category]
            path = KB_DIR / filename
            return StructuredMatch(
                category=category,
                content=path.read_text(encoding="utf-8"),
                source_file=filename,
            )
    return None
