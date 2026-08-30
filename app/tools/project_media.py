"""Per-project media overlay for POST /chat.

Paths are frontend-relative (public/ on the landing). This API does not host
or rewrite them — the client prefixes its own origin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ImageFrame = Literal["phone", "browser"]


@dataclass(frozen=True)
class MediaImage:
    path: str
    frame: ImageFrame
    alt: str


@dataclass(frozen=True)
class ProjectMedia:
    key: str
    link: str
    aliases: tuple[str, ...]
    images: tuple[MediaImage, ...]


@dataclass(frozen=True)
class CarouselItem:
    id: str
    title: str
    category: str
    cover_image: str | None
    cover_gradient: tuple[str, str] | None
    link: str | None


# General Projects shortcut only. Mutually exclusive with PROJECT_MEDIA attachments.
PROJECT_CAROUSEL: tuple[CarouselItem, ...] = (
    CarouselItem(
        id="velox",
        title="Velox",
        category="AI Product",
        cover_image="/projects/velox/dashboard-overview.png",
        cover_gradient=None,
        link="https://velox-rag-lending.vercel.app",
    ),
    CarouselItem(
        id="saasaimenu",
        title="SaaSAiMenu",
        category="SaaS Platform",
        cover_image=None,
        cover_gradient=("#4c6ef5", "#3ecf8e"),
        link=None,
    ),
    CarouselItem(
        id="ai-chaina",
        title="AI-CHAINA",
        category="Automation",
        cover_image=None,
        cover_gradient=("#ff6ec7", "#ff9f43"),
        link=None,
    ),
    CarouselItem(
        id="amocrm",
        title="amoCRM Automations",
        category="CRM Integration",
        cover_image=None,
        cover_gradient=("#3ecf8e", "#4c6ef5"),
        link=None,
    ),
    CarouselItem(
        id="hh-bot",
        title="hh.ru Job Bot",
        category="Job Automation",
        cover_image=None,
        cover_gradient=("#ff9f43", "#ff6ec7"),
        link=None,
    ),
    CarouselItem(
        id="video-autoposting",
        title="Video Autoposting",
        category="Automation Tool",
        cover_image=None,
        cover_gradient=("#4c6ef5", "#ff6ec7"),
        link=None,
    ),
)


# Only projects listed here can produce a non-null attachments payload.
PROJECT_MEDIA: dict[str, ProjectMedia] = {
    "velox": ProjectMedia(
        key="velox",
        link="https://velox-rag-lending.vercel.app",
        aliases=("velox", "велокс"),
        images=(
            MediaImage(
                path="/projects/velox/tma-readiness.png",
                frame="phone",
                alt="Экран готовности к тренировке",
            ),
            MediaImage(
                path="/projects/velox/tma-neurotrainer.png",
                frame="phone",
                alt="Чат с AI-тренером в мобильном приложении",
            ),
            MediaImage(
                path="/projects/velox/dashboard-overview.png",
                frame="browser",
                alt="Обзорный дашборд метрик",
            ),
            MediaImage(
                path="/projects/velox/dashboard-neurotrainer.png",
                frame="browser",
                alt="Разбор тренировки AI-тренером в веб-версии",
            ),
        ),
    ),
}
