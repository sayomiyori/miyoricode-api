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
