"""Per-project media overlay for POST /chat.

Local paths are frontend-relative (public/ on the landing). GitHub screenshots
use raw.githubusercontent.com so next/image can fetch them without a 302.
This API does not host or rewrite either kind — the client prefixes its own
origin for local paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ImageFrame = Literal["phone", "browser"]

_GH = "https://raw.githubusercontent.com/sayomiyori"


def _raw(repo: str, name: str) -> str:
    return f"{_GH}/{repo}/main/docs/images/{name}"


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
class CarouselLink:
    label: str
    url: str


@dataclass(frozen=True)
class CarouselItem:
    id: str
    title: str
    category: str
    year: str
    cover_image: str | None
    cover_gradient: tuple[str, str] | None
    description: str
    technologies: tuple[str, ...]
    link: str | None
    links: tuple[CarouselLink, ...]
    screenshots: tuple[MediaImage, ...]


_VELOX_IMAGES: tuple[MediaImage, ...] = (
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
)

_AGENTHUB_SHOTS: tuple[MediaImage, ...] = (
    MediaImage(
        path=_raw("AgentHub", "rag-query-result.png"),
        frame="browser",
        alt="Результат RAG-запроса в AgentHub",
    ),
    MediaImage(
        path=_raw("AgentHub", "swagger-ui.png"),
        frame="browser",
        alt="Swagger UI AgentHub",
    ),
    MediaImage(
        path=_raw("AgentHub", "grafana-dashboard.png"),
        frame="browser",
        alt="Grafana-дашборд AgentHub",
    ),
    MediaImage(
        path=_raw("AgentHub", "agent-rag-query.png"),
        frame="browser",
        alt="AI-агент выполняет RAG-запрос",
    ),
)

_AUTHFORTRESS_SHOTS: tuple[MediaImage, ...] = (
    MediaImage(
        path=_raw("AuthFortress", "swagger-ui.png"),
        frame="browser",
        alt="Swagger UI AuthFortress",
    ),
    MediaImage(
        path=_raw("AuthFortress", "admin-users.png"),
        frame="browser",
        alt="Админка пользователей",
    ),
    MediaImage(
        path=_raw("AuthFortress", "audit-log.png"),
        frame="browser",
        alt="Аудит-лог событий",
    ),
    MediaImage(
        path=_raw("AuthFortress", "docker-services.png"),
        frame="browser",
        alt="Docker-сервисы AuthFortress",
    ),
)

_NEURO_SHOTS: tuple[MediaImage, ...] = (
    MediaImage(
        path=_raw("NeuroClassifier", "swagger-ui.png"),
        frame="browser",
        alt="Swagger UI NeuroClassifier",
    ),
    MediaImage(
        path=_raw("NeuroClassifier", "dataset-list.png"),
        frame="browser",
        alt="Список датасетов",
    ),
    MediaImage(
        path=_raw("NeuroClassifier", "minio-datasets.png"),
        frame="browser",
        alt="Датасеты в MinIO",
    ),
)

_EVENTPIPE_SHOTS: tuple[MediaImage, ...] = (
    MediaImage(
        path=_raw("EventPipe", "swagger-ingest.png"),
        frame="browser",
        alt="Swagger Ingest API EventPipe",
    ),
    MediaImage(
        path=_raw("EventPipe", "grafana-dashboard.png"),
        frame="browser",
        alt="Grafana-дашборд EventPipe",
    ),
    MediaImage(
        path=_raw("EventPipe", "docker-services-phase1.png"),
        frame="browser",
        alt="Docker-сервисы EventPipe",
    ),
    MediaImage(
        path=_raw("EventPipe", "k8s-pods.png"),
        frame="browser",
        alt="Поды EventPipe в Kubernetes",
    ),
    MediaImage(
        path=_raw("EventPipe", "kafka-consumer.png"),
        frame="browser",
        alt="Kafka consumer EventPipe",
    ),
)


# General Projects shortcut only. Mutually exclusive with PROJECT_MEDIA attachments.
PROJECT_CAROUSEL: tuple[CarouselItem, ...] = (
    CarouselItem(
        id="velox",
        title="Velox",
        category="AI Product",
        year="2026",
        cover_image="/projects/velox/dashboard-overview.png",
        cover_gradient=None,
        description=(
            "AI-платформа для бегунов с персональным нейротренером. Продакшен-система "
            "с двойным интерфейсом (Telegram Mini App + веб), построенная с нуля за "
            "апрель-май 2026. RAG-система на 4 персонажа-тренера с персонализированными "
            "промптами, SSE-стримингом ответов и суммаризацией памяти диалога. Полный "
            "цикл спортивной аналитики: метрики нагрузки CTL/ATL/FORM/ACWR как у "
            "профессиональных платформ, система эскалации по HRV, анализ тренировок с "
            "детекцией личных рекордов и автопересчётом VDOT, генерация тренировочных "
            "планов, модуль анализа крови. Интеграция со Strava (полностью прошла их "
            "compliance-проверку: deauth webhook, brand assets, страницы приватности). "
            "Отдельно горжусь оптимизацией инференса — кэширование системного промпта "
            "снизило стоимость на 93% на сообщение, плюс каскад лёгкая/тяжёлая модель "
            "под сложность запроса — оба показателя подтверждены на реальном биллинге, "
            "не оценочно."
        ),
        technologies=(
            "FastAPI",
            "React",
            "TypeScript",
            "aiogram 3",
            "Docker",
            "Qdrant",
            "text-embedding-3-large",
            "BM25",
            "Claude API",
        ),
        link="https://velox-rag-lending.vercel.app",
        links=(),
        screenshots=_VELOX_IMAGES,
    ),
    CarouselItem(
        id="saasaimenu",
        title="SaaSAiMenu (Maitre)",
        category="SaaS Platform",
        year="2026",
        cover_image=None,
        cover_gradient=("#4c6ef5", "#3ecf8e"),
        description=(
            "Мультитенантная SaaS-платформа QR-меню для премиальных ресторанов, "
            "готовится к запуску в Москве. AI-агент-официант на function calling "
            "(Anthropic API) поверх базы блюд — допродажи, ответы про состав и "
            "аллергены, без vector RAG (не требуется при текущем объёме каталога). "
            "Отдельная фича — генерация 3D-моделей блюд из фото через Meshy AI с "
            "вьювером на Three.js, с оптимизацией под мобильный WebGL. Заказы в "
            "реальном времени через WebSocket, админка с аналитикой (топ блюд, "
            "выручка, пиковые часы) и AI-рекомендациями по ценообразованию. "
            "Двухсерверная инфраструктура (Россия + Amsterdam) для обхода сетевой "
            "фильтрации к внешним AI API. Прошёл security-аудит: 49 из 49 тестов, "
            "0 критичных уязвимостей."
        ),
        technologies=(
            "FastAPI",
            "SQLAlchemy 2 async",
            "PostgreSQL",
            "PgBouncer",
            "Redis",
            "Celery",
            "Next.js",
            "React",
            "Anthropic API",
            "Meshy AI",
            "Three.js",
        ),
        link=None,
        links=(),
        screenshots=(),
    ),
    CarouselItem(
        id="ai-chaina",
        title="AI-CHAINA",
        category="Automation",
        year="2026",
        cover_image=None,
        cover_gradient=("#ff6ec7", "#ff9f43"),
        description=(
            "Полная автоматизация документооборота для импортёра из Китая — то, "
            "что раньше делалось вручную, теперь работает без участия человека. "
            "Считает таможенные платежи, логистику и комиссии, генерирует 4 типа "
            "финансовых документов на сделку, обновляет их при изменении данных в "
            "CRM. Технически интересная часть — асинхронный пайплайн через очередь "
            "сообщений с учётом жёсткого 2-секундного лимита на ответ вебхука "
            "amoCRM; защита от дублей через SHA-256 хеш состояния сделки с debounce; "
            "распределённые блокировки через S3 ETag для потокобезопасного "
            "обновления OAuth-токенов; решение cold start в serverless-окружении; "
            "интеграция кастомного formula-движка amoCRM для realtime-расчётов "
            "прямо в интерфейсе CRM. Работает в продакшене, весь цикл от создания "
            "сделки до готовых документов верифицирован end-to-end."
        ),
        technologies=(
            "FastAPI",
            "Yandex Cloud Serverless",
            "amoCRM API",
            "Google Drive API",
            "structlog",
            "reportlab",
        ),
        link=None,
        links=(),
        screenshots=(),
    ),
    CarouselItem(
        id="amocrm",
        title="amoCRM Automations",
        category="CRM Integration",
        year="2026",
        cover_image=None,
        cover_gradient=("#3ecf8e", "#4c6ef5"),
        description=(
            "Серия проектов по автоматизации amoCRM для нескольких клиентов. "
            "Микросервисы отчётности с еженедельными AI-сводками по сделкам "
            "(LLM-суммаризация), health-эндпоинтами и структурированным "
            "логированием. Интеграции TravelLine↔amoCRM и TravelLine↔внешние боты "
            "продаж для курортного бизнеса. С нуля выстроенные воронки под "
            "ВЭД-импорт из Китая — от предварительного расчёта до приёмки товара, "
            "с автозадачами менеджеру и блокировкой перехода между этапами без "
            "загруженных документов. Плюс смежные боты для тех же клиентов: "
            "торговый бот, бот отчётности по CRM-системе бьюти-индустрии."
        ),
        technologies=("amoCRM API", "OpenAI API", "FastAPI", "Docker", "Celery"),
        link=None,
        links=(),
        screenshots=(),
    ),
    CarouselItem(
        id="hh-bot",
        title="hh.ru Job Automation",
        category="Job Automation",
        year="2026",
        cover_image=None,
        cover_gradient=("#ff9f43", "#ff6ec7"),
        description=(
            "Автоматизация отклика на вакансии на hh.ru. Celery + Playwright + "
            "RedBeat scheduler, ежедневные Telegram-отчёты, авто-релогин, "
            "watchdog-скрипт для мониторинга состояния. Отдельный модуль поверх "
            "этого — генерация персонализированных сопроводительных писем через "
            "LLM на основе резюме и текста конкретной вакансии, с уведомлениями "
            "через Telegram-бота."
        ),
        technologies=("Celery", "Playwright", "RedBeat", "Claude API", "aiogram"),
        link=None,
        links=(),
        screenshots=(),
    ),
    CarouselItem(
        id="video-autoposting",
        title="Video Autoposting",
        category="Automation Tool",
        year="2026",
        cover_image=None,
        cover_gradient=("#4c6ef5", "#ff6ec7"),
        description=(
            "Сервис автоматической публикации видео на несколько платформ "
            "одновременно для агентства-клиента. Мультипрофильная архитектура с "
            "визуализацией браузера через KasmVNC, интеграция с Google Drive/Sheets, "
            "шифрование учётных данных профилей (Fernet). Дашборд на Next.js + "
            "FastAPI с логами в реальном времени через WebSocket."
        ),
        technologies=(
            "Python",
            "Playwright",
            "aiogram",
            "Docker",
            "KasmVNC",
            "Next.js",
            "FastAPI",
            "WebSocket",
        ),
        link=None,
        links=(),
        screenshots=(),
    ),
    CarouselItem(
        id="agenthub",
        title="AgentHub",
        category="Pet Project",
        year="2026",
        cover_image=_raw("AgentHub", "rag-query-result.png"),
        cover_gradient=("#4c6ef5", "#3ecf8e"),
        description=(
            "AI-платформа с RAG-пайплайном (pgvector + семантический поиск + "
            "reranking), AI-агентами на function calling, MCP-сервером (SSE) и "
            "мультипровайдерным роутингом LLM (Gemini/Anthropic/OpenAI). Есть "
            "семантический кэш на Redis (LSH-бакеты, cosine ≥0.95) и трекинг "
            "стоимости токенов по провайдеру/модели/дню. Архитектурно интересно: "
            "pgvector вместо отдельной vector DB — вся модель данных в одном "
            "PostgreSQL, транзакционная согласованность между метаданными "
            "документов и эмбеддингами. MCP-сервер позволяет внешним агентам "
            "(Claude Desktop, Cursor) использовать базу знаний AgentHub как инструмент."
        ),
        technologies=(
            "FastAPI",
            "PostgreSQL",
            "pgvector",
            "SQLAlchemy 2",
            "Celery",
            "Redis",
            "Gemini API",
            "Anthropic API",
            "OpenAI API",
            "MCP",
            "Prometheus",
            "Grafana",
        ),
        link=None,
        links=(
            CarouselLink(label="GitHub", url="https://github.com/sayomiyori/AgentHub"),
        ),
        screenshots=_AGENTHUB_SHOTS,
    ),
    CarouselItem(
        id="authfortress",
        title="AuthFortress",
        category="Pet Project",
        year="2025",
        cover_image=_raw("AuthFortress", "swagger-ui.png"),
        cover_gradient=("#ff9f43", "#4c6ef5"),
        description=(
            "Продакшен-готовый auth-микросервис: JWT-сессии с ротацией refresh-токенов, "
            "OAuth2 (Google/GitHub/Yandex), TOTP 2FA с backup-кодами, RBAC-иерархия "
            "(user/admin/superadmin), аудит-лог на 15+ событий, rate limiting на "
            "скользящем окне через Redis, Prometheus-метрики. Каждый вызов "
            "/auth/refresh валидирует старый токен по SHA-256 хешу, выдаёт новую "
            "пару и немедленно инвалидирует старый — повторное использование "
            "возвращает 401."
        ),
        technologies=(
            "FastAPI",
            "PostgreSQL",
            "Redis",
            "JWT",
            "OAuth2",
            "TOTP",
            "Docker",
            "Prometheus",
        ),
        link=None,
        links=(
            CarouselLink(
                label="GitHub",
                url="https://github.com/sayomiyori/AuthFortress",
            ),
        ),
        screenshots=_AUTHFORTRESS_SHOTS,
    ),
    CarouselItem(
        id="neuroclassifier",
        title="NeuroClassifier",
        category="Pet Project",
        year="2025",
        cover_image=_raw("NeuroClassifier", "swagger-ui.png"),
        cover_gradient=("#ff6ec7", "#4c6ef5"),
        description=(
            "ML-платформа инференса: загрузка датасета → LoRA fine-tune vision "
            "transformer в фоне → отдача предсказаний через ONNX Runtime — всё "
            "через единый REST API. Асинхронное обучение на Celery, реестр моделей "
            "в MinIO, мониторинг Prometheus/Grafana. LoRA обучает только ~1% "
            "параметров модели, что позволяет сходиться за минуты на CPU без GPU. "
            "ONNX Runtime даёт инференс в 3-5 раз быстрее обычного PyTorch "
            "forward-прохода."
        ),
        technologies=(
            "FastAPI",
            "PyTorch",
            "HuggingFace",
            "PEFT/LoRA",
            "ONNX Runtime",
            "Celery",
            "MinIO",
            "PostgreSQL",
            "Prometheus",
            "Grafana",
        ),
        link=None,
        links=(
            CarouselLink(
                label="GitHub",
                url="https://github.com/sayomiyori/NeuroClassifier",
            ),
        ),
        screenshots=_NEURO_SHOTS,
    ),
    CarouselItem(
        id="eventpipe",
        title="EventPipe",
        category="Pet Project",
        year="2025",
        cover_image=_raw("EventPipe", "grafana-dashboard.png"),
        cover_gradient=("#3ecf8e", "#ff6ec7"),
        description=(
            "Микросервисный ETL-пайплайн: приём событий (FastAPI REST + gRPC) → "
            "Kafka → трансформация (валидация/обогащение/нормализация) → "
            "PostgreSQL + MinIO, с Query API, Dead Letter Queue и мониторингом "
            "Prometheus/Grafana. Три независимых сервиса (Ingest/Transform/Query) "
            "с разным профилем нагрузки масштабируются отдельно. Развёрнуто и на "
            "Docker Compose, и на Kubernetes (манифесты + горизонтальное "
            "масштабирование Transform-воркеров по партициям Kafka)."
        ),
        technologies=(
            "FastAPI",
            "gRPC",
            "Apache Kafka",
            "PostgreSQL",
            "MinIO",
            "Kubernetes",
            "Docker",
            "Prometheus",
            "Grafana",
        ),
        link=None,
        links=(
            CarouselLink(label="GitHub", url="https://github.com/sayomiyori/EventPipe"),
        ),
        screenshots=_EVENTPIPE_SHOTS,
    ),
)


# Only projects listed here can produce a non-null attachments payload.
PROJECT_MEDIA: dict[str, ProjectMedia] = {
    "velox": ProjectMedia(
        key="velox",
        link="https://velox-rag-lending.vercel.app",
        aliases=("velox", "велокс"),
        images=_VELOX_IMAGES,
    ),
}
