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
    # Language-invariant English labels ("AI Product", "SaaS Platform").
    # Shown as-is on both EN and RU UI — not localized.
    category: str
    year: str
    cover_image: str | None
    cover_gradient: tuple[str, str] | None
    description_ru: str
    description_en: str
    # Language-invariant proper names (FastAPI, Redis, …).
    technologies: tuple[str, ...]
    link: str | None
    links: tuple[CarouselLink, ...]
    screenshots: tuple[MediaImage, ...]

    def localized_description(self, lang: str) -> str:
        return self.description_en if lang == "en" else self.description_ru


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
        description_ru=(
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
        description_en=(
            "AI platform for runners with a personal neurotrainer. A production system "
            "with a dual interface (Telegram Mini App + web), built from scratch in "
            "April–May 2026. RAG system with 4 trainer personas, personalized prompts, "
            "SSE-streamed replies, and dialogue-memory summarization. Full sports-analytics "
            "cycle: load metrics CTL/ATL/FORM/ACWR like professional platforms, HRV-based "
            "escalation, workout analysis with personal-record detection and automatic "
            "VDOT recalculation, training-plan generation, blood-work analysis module. "
            "Strava integration (passed their full compliance review: deauth webhook, "
            "brand assets, privacy pages). I'm especially proud of the inference "
            "optimization — system-prompt caching cut cost by 93% per message, plus a "
            "light/heavy model cascade by query complexity — both numbers confirmed on "
            "real billing, not estimates."
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
        description_ru=(
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
        description_en=(
            "Multi-tenant SaaS QR-menu platform for premium restaurants, preparing "
            "to launch in Moscow. AI waiter agent on function calling (Anthropic API) "
            "over the dish catalog — upsells, answers about ingredients and allergens, "
            "no vector RAG (not needed at the current catalog size). A separate feature "
            "generates 3D dish models from photos via Meshy AI with a Three.js viewer, "
            "optimized for mobile WebGL. Real-time orders over WebSocket, an admin "
            "dashboard with analytics (top dishes, revenue, peak hours) and AI pricing "
            "recommendations. Dual-server setup (Russia + Amsterdam) to reach external "
            "AI APIs through network filtering. Passed a security audit: 49 of 49 tests, "
            "0 critical vulnerabilities."
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
        description_ru=(
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
        description_en=(
            "Full document-flow automation for a China importer — what used to be "
            "done by hand now runs without a person in the loop. It calculates customs "
            "payments, logistics, and commissions, generates 4 types of financial "
            "documents per deal, and updates them when CRM data changes. The technically "
            "interesting part: an async pipeline through a message queue that respects "
            "amoCRM's hard 2-second webhook response limit; duplicate protection via a "
            "SHA-256 hash of deal state with debounce; distributed locks via S3 ETag "
            "for thread-safe OAuth token refresh; a serverless cold-start workaround; "
            "and a custom amoCRM formula-engine integration for realtime calculations "
            "inside the CRM UI. In production; the full cycle from deal creation to "
            "finished documents is verified end-to-end."
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
        description_ru=(
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
        description_en=(
            "A series of amoCRM automation projects for several clients. Reporting "
            "microservices with weekly AI deal summaries (LLM summarization), health "
            "endpoints, and structured logging. TravelLine↔amoCRM and TravelLine↔external "
            "sales-bot integrations for resort businesses. Funnels built from scratch "
            "for foreign trade / import-export from China — from preliminary calculation "
            "to goods acceptance, with auto-tasks for the manager and stage-transition "
            "locks until documents are uploaded. Plus related bots for the same clients: "
            "a trading bot and a reporting bot for a beauty-industry CRM."
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
        description_ru=(
            "Автоматизация отклика на вакансии на hh.ru. Celery + Playwright + "
            "RedBeat scheduler, ежедневные Telegram-отчёты, авто-релогин, "
            "watchdog-скрипт для мониторинга состояния. Отдельный модуль поверх "
            "этого — генерация персонализированных сопроводительных писем через "
            "LLM на основе резюме и текста конкретной вакансии, с уведомлениями "
            "через Telegram-бота."
        ),
        description_en=(
            "Job-application automation on hh.ru. Celery + Playwright + RedBeat "
            "scheduler, daily Telegram reports, auto-relogin, a watchdog script for "
            "health monitoring. A separate module on top generates personalized cover "
            "letters via LLM from the résumé and the specific vacancy text, with "
            "notifications through a Telegram bot."
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
        description_ru=(
            "Сервис автоматической публикации видео на несколько платформ "
            "одновременно для агентства-клиента. Мультипрофильная архитектура с "
            "визуализацией браузера через KasmVNC, интеграция с Google Drive/Sheets, "
            "шифрование учётных данных профилей (Fernet). Дашборд на Next.js + "
            "FastAPI с логами в реальном времени через WebSocket."
        ),
        description_en=(
            "A service that publishes videos to several platforms at once for an "
            "agency client. Multi-profile architecture with browser visualization via "
            "KasmVNC, Google Drive/Sheets integration, Fernet encryption of profile "
            "credentials. Next.js + FastAPI dashboard with realtime logs over WebSocket."
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
        description_ru=(
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
        description_en=(
            "AI platform with a RAG pipeline (pgvector + semantic search + reranking), "
            "function-calling AI agents, an MCP server (SSE), and multi-provider LLM "
            "routing (Gemini/Anthropic/OpenAI). Semantic cache on Redis (LSH buckets, "
            "cosine ≥0.95) and token-cost tracking by provider/model/day. Architecturally "
            "interesting: pgvector instead of a separate vector DB — the whole data model "
            "lives in one PostgreSQL, with transactional consistency between document "
            "metadata and embeddings. The MCP server lets external agents (Claude Desktop, "
            "Cursor) use the AgentHub knowledge base as a tool."
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
        description_ru=(
            "Продакшен-готовый auth-микросервис: JWT-сессии с ротацией refresh-токенов, "
            "OAuth2 (Google/GitHub/Yandex), TOTP 2FA с backup-кодами, RBAC-иерархия "
            "(user/admin/superadmin), аудит-лог на 15+ событий, rate limiting на "
            "скользящем окне через Redis, Prometheus-метрики. Каждый вызов "
            "/auth/refresh валидирует старый токен по SHA-256 хешу, выдаёт новую "
            "пару и немедленно инвалидирует старый — повторное использование "
            "возвращает 401."
        ),
        description_en=(
            "Production-ready auth microservice: JWT sessions with refresh-token "
            "rotation, OAuth2 (Google/GitHub/Yandex), TOTP 2FA with backup codes, "
            "RBAC hierarchy (user/admin/superadmin), audit log of 15+ events, "
            "sliding-window rate limiting via Redis, Prometheus metrics. Every "
            "/auth/refresh call validates the old token by SHA-256 hash, issues a new "
            "pair, and immediately invalidates the old one — reuse returns 401."
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
        description_ru=(
            "ML-платформа инференса: загрузка датасета → LoRA fine-tune vision "
            "transformer в фоне → отдача предсказаний через ONNX Runtime — всё "
            "через единый REST API. Асинхронное обучение на Celery, реестр моделей "
            "в MinIO, мониторинг Prometheus/Grafana. LoRA обучает только ~1% "
            "параметров модели, что позволяет сходиться за минуты на CPU без GPU. "
            "ONNX Runtime даёт инференс в 3-5 раз быстрее обычного PyTorch "
            "forward-прохода."
        ),
        description_en=(
            "ML inference platform: upload a dataset → LoRA fine-tune a vision "
            "transformer in the background → serve predictions via ONNX Runtime — all "
            "through a single REST API. Async training on Celery, model registry in "
            "MinIO, Prometheus/Grafana monitoring. LoRA trains only ~1% of model "
            "parameters, so it converges in minutes on CPU without a GPU. ONNX Runtime "
            "inference is 3–5× faster than a regular PyTorch forward pass."
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
        description_ru=(
            "Микросервисный ETL-пайплайн: приём событий (FastAPI REST + gRPC) → "
            "Kafka → трансформация (валидация/обогащение/нормализация) → "
            "PostgreSQL + MinIO, с Query API, Dead Letter Queue и мониторингом "
            "Prometheus/Grafana. Три независимых сервиса (Ingest/Transform/Query) "
            "с разным профилем нагрузки масштабируются отдельно. Развёрнуто и на "
            "Docker Compose, и на Kubernetes (манифесты + горизонтальное "
            "масштабирование Transform-воркеров по партициям Kafka)."
        ),
        description_en=(
            "Microservice ETL pipeline: ingest events (FastAPI REST + gRPC) → Kafka → "
            "transform (validation/enrichment/normalization) → PostgreSQL + MinIO, "
            "with a Query API, Dead Letter Queue, and Prometheus/Grafana monitoring. "
            "Three independent services (Ingest/Transform/Query) with different load "
            "profiles scale separately. Deployed on both Docker Compose and Kubernetes "
            "(manifests + horizontal scaling of Transform workers by Kafka partition)."
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
