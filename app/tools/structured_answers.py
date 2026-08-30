from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.tools.project_media import PROJECT_CAROUSEL, PROJECT_MEDIA, ProjectMedia

KB_DIR = Path(__file__).resolve().parent.parent / "rag" / "knowledge_base"

CATEGORY_FILES = {
    "me": "me.md",
    "projects": "projects.md",
    "skills": "skills.md",
    "fun": "fun.md",
    "contact": "contact.md",
    "faq": "faq.md",
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
    ("какие у тебя проекты", "projects"),
    ("какие проекты", "projects"),
    ("про проекты", "projects"),
    ("проекты", "projects"),
    ("skills", "skills"),
    ("your skills", "skills"),
    ("tell me about your skills", "skills"),
    ("what's your tech stack", "skills"),
    ("what is your tech stack", "skills"),
    ("навыки", "skills"),
    ("скиллы", "skills"),
    ("расскажи о навыках", "skills"),
    ("какой стек используешь", "skills"),
    ("какой стек", "skills"),
    ("стек", "skills"),
    ("fun", "fun"),
    ("fun facts", "fun"),
    ("something fun", "fun"),
    ("пошути", "fun"),
    ("для души", "fun"),
    ("contact", "contact"),
    ("how to contact", "contact"),
    ("how can i reach you", "contact"),
    ("как с тобой связаться", "contact"),
    ("связаться", "contact"),
    ("контакты", "contact"),
    ("faq", "faq"),
    ("are you ready to relocate", "faq"),
    ("ready to relocate", "faq"),
    ("готов к переезду", "faq"),
    ("переезд", "faq"),
]


@dataclass(frozen=True)
class StructuredMatch:
    category: str
    content: str
    source_file: str


def _alias_pattern(project: ProjectMedia) -> re.Pattern[str]:
    escaped = "|".join(re.escape(alias) for alias in project.aliases)
    return re.compile(rf"(?iu)\b(?:{escaped})\b")


_PROJECT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (key, _alias_pattern(project)) for key, project in PROJECT_MEDIA.items()
)


def _attachments_payload(project: ProjectMedia) -> dict[str, Any]:
    return {
        "link": project.link,
        "images": [
            {"url": image.path, "frame": image.frame, "alt": image.alt}
            for image in project.images
        ],
    }


def _carousel_payload() -> dict[str, Any]:
    return {
        "type": "project_carousel",
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "category": item.category,
                "year": item.year,
                "cover_image": item.cover_image,
                "cover_gradient": list(item.cover_gradient) if item.cover_gradient else None,
                "description": item.description,
                "technologies": list(item.technologies),
                "link": item.link,
                "links": [
                    {"label": link.label, "url": link.url} for link in item.links
                ],
                "screenshots": [
                    {"url": image.path, "frame": image.frame, "alt": image.alt}
                    for image in item.screenshots
                ],
            }
            for item in PROJECT_CAROUSEL
        ],
    }


def match_attachments(message: str) -> dict[str, Any] | None:
    """Overlay after the text reply is chosen.

    Inspects the user question only. A general Projects shortcut does not
    mention a catalog key, so attachments stay null even if the KB text
    talks about Velox. Explicit Velox / велокс still attaches on RAG turns.
    """
    if not message.strip():
        return None
    for key, pattern in _PROJECT_PATTERNS:
        if pattern.search(message):
            return _attachments_payload(PROJECT_MEDIA[key])
    return None


def match_project_carousel(message: str) -> dict[str, Any] | None:
    """Carousel for the general Projects shortcut only.

    Never overlaps with attachments: a named project (Velox, SaaSAiMenu, …)
    skips the carousel and keeps the existing per-project overlay.
    """
    structured = match_structured(message)
    if structured is None or structured.category != "projects":
        return None
    if match_attachments(message) is not None:
        return None
    return _carousel_payload()


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
