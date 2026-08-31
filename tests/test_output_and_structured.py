import re

from app.config import Settings
from app.guardrail.output_filter import filter_output
from app.guardrail.system_prompt import CANARY
from app.tools.project_media import PROJECT_CAROUSEL
from app.tools.structured_answers import (
    match_attachments,
    match_project_carousel,
    match_structured,
)

_CYRILLIC = re.compile(r"[А-Яа-яЁё]")


def test_output_filter_catches_canary():
    settings = Settings()
    text, leaked = filter_output(f"Here is {CANARY} and the rules", "en", settings)
    assert leaked
    assert "professional experience" in text.lower()


def test_output_filter_truncates_long_reply():
    settings = Settings(max_reply_words=5, max_reply_chars=200)
    text, leaked = filter_output("one two three four five six seven", "en", settings)
    assert not leaked
    assert text.endswith("…")
    assert len(text.split()) <= 6


def test_output_filter_skips_length_when_not_enforced():
    settings = Settings(max_reply_words=5, max_reply_chars=20)
    long = " ".join(["word"] * 40)
    text, leaked = filter_output(long, "en", settings, enforce_length=False)
    assert not leaked
    assert text == long
    assert not text.endswith("…")


def test_structured_prompt_is_faithful_translation_without_word_cap():
    from app.guardrail.system_prompt import build_system_prompt

    settings = Settings()
    prompt = build_system_prompt("en", settings, source="structured")
    assert "as faithfully as possible" in prompt
    assert "150 words" not in prompt
    assert "URLs, links, and proper names must be copied exactly" in prompt
    assert "first person" in prompt.lower()
    assert "Yes, I'm ready to relocate" in prompt
    assert "never transliterated" in prompt
    assert "ВЭД → foreign trade / import-export business" in prompt


def test_russian_prompt_omits_english_glossary():
    from app.guardrail.system_prompt import build_system_prompt

    settings = Settings()
    prompt = build_system_prompt("ru", settings, source="structured")
    assert "never transliterated" not in prompt
    assert "foreign trade / import-export business" not in prompt


def test_rag_prompt_keeps_word_cap_and_first_person():
    from app.guardrail.system_prompt import build_system_prompt

    settings = Settings()
    prompt = build_system_prompt("en", settings, source="rag")
    assert "150 words" in prompt
    assert "first person" in prompt.lower()
    assert "as faithfully as possible" not in prompt


def test_structured_match_projects_ru():
    match = match_structured("расскажи о проектах")
    assert match is not None
    assert match.source_file == "projects.md"
    assert "Velox" in match.content


def test_structured_match_paraphrases():
    projects = match_structured("какие у тебя проекты")
    assert projects is not None
    assert projects.source_file == "projects.md"
    skills = match_structured("какой стек используешь")
    assert skills is not None
    assert skills.source_file == "skills.md"
    stack_en = match_structured("what's your tech stack")
    assert stack_en is not None
    assert stack_en.source_file == "skills.md"
    relocate = match_structured("are you ready to relocate?")
    assert relocate is not None
    assert relocate.source_file == "faq.md"
    contact = match_structured("как с тобой связаться")
    assert contact is not None
    assert contact.source_file == "contact.md"


def test_structured_match_ignores_freeform():
    assert match_structured("how did you design the RAG chunk overlap?") is None
    assert match_structured("расскажи про Velox") is None
    assert match_structured("tell me about Velox") is None


def _assert_velox_attachments(payload: dict) -> None:
    assert payload["link"] == "https://velox-rag-lending.vercel.app"
    urls = [item["url"] for item in payload["images"]]
    assert urls == [
        "/projects/velox/tma-readiness.png",
        "/projects/velox/tma-neurotrainer.png",
        "/projects/velox/dashboard-overview.png",
        "/projects/velox/dashboard-neurotrainer.png",
    ]
    assert [item["frame"] for item in payload["images"]] == [
        "phone",
        "phone",
        "browser",
        "browser",
    ]
    assert all(item["alt"] for item in payload["images"])


def test_attachments_on_explicit_velox_mention():
    for message in (
        "tell me about Velox",
        "расскажи про Velox",
        "расскажи про велокс",
        "VELOX dashboard",
    ):
        payload = match_attachments(message)
        assert payload is not None, message
        _assert_velox_attachments(payload)


def test_attachments_null_for_general_projects_and_other_work():
    assert match_attachments("расскажи про проекты") is None
    assert match_attachments("Tell me about your projects") is None
    assert match_attachments("расскажи про SaaSAiMenu") is None
    assert match_attachments("what is Maitre / AI-CHAINA?") is None
    assert match_attachments("veloxian training plan") is None


_CAROUSEL_IDS = (
    "velox",
    "saasaimenu",
    "ai-chaina",
    "amocrm",
    "hh-bot",
    "video-autoposting",
    "agenthub",
    "authfortress",
    "neuroclassifier",
    "eventpipe",
)
_CAROUSEL_TITLES = (
    "Velox",
    "SaaSAiMenu (Maitre)",
    "AI-CHAINA",
    "amoCRM Automations",
    "hh.ru Job Automation",
    "Video Autoposting",
    "AgentHub",
    "AuthFortress",
    "NeuroClassifier",
    "EventPipe",
)
_CAROUSEL_CATEGORIES = (
    "AI Product",
    "SaaS Platform",
    "Automation",
    "CRM Integration",
    "Job Automation",
    "Automation Tool",
    "Pet Project",
    "Pet Project",
    "Pet Project",
    "Pet Project",
)


def _assert_project_carousel(payload: dict) -> None:
    assert payload["type"] == "project_carousel"
    items = payload["items"]
    assert len(items) == 10
    assert [item["id"] for item in items] == list(_CAROUSEL_IDS)
    assert [item["title"] for item in items] == list(_CAROUSEL_TITLES)
    assert [item["category"] for item in items] == list(_CAROUSEL_CATEGORIES)
    velox = items[0]
    assert velox["cover_image"] == "/projects/velox/dashboard-overview.png"
    assert velox["cover_gradient"] is None
    assert velox["link"] == "https://velox-rag-lending.vercel.app"
    assert velox["year"] == "2026"
    assert velox["description"]
    assert "FastAPI" in velox["technologies"]
    assert len(velox["screenshots"]) == 4
    assert velox["screenshots"][0]["frame"] == "phone"
    saas = items[1]
    assert saas["cover_image"] is None
    assert saas["cover_gradient"] == ["#4c6ef5", "#3ecf8e"]
    assert saas["link"] is None
    assert saas["screenshots"] == []
    agenthub = items[6]
    assert agenthub["category"] == "Pet Project"
    assert agenthub["links"] == [
        {"label": "GitHub", "url": "https://github.com/sayomiyori/AgentHub"}
    ]
    assert agenthub["cover_image"].startswith(
        "https://raw.githubusercontent.com/sayomiyori/AgentHub/"
    )
    assert all(
        shot["url"].startswith("https://raw.githubusercontent.com/sayomiyori/")
        and shot["frame"] == "browser"
        and shot["alt"]
        for shot in agenthub["screenshots"]
    )
    assert len(agenthub["screenshots"]) == 4


def test_carousel_on_general_projects_shortcut():
    for message in (
        "Tell me about your projects",
        "расскажи о проектах",
        "projects",
        "проекты",
    ):
        payload = match_project_carousel(message, lang="ru")
        assert payload is not None, message
        _assert_project_carousel(payload)


def test_carousel_null_for_named_project_and_freeform():
    assert match_project_carousel("Tell me about Velox", lang="en") is None
    assert match_project_carousel("tell me about Velox", lang="en") is None
    assert match_project_carousel("Tell me about SaaSAiMenu", lang="en") is None
    assert match_project_carousel("расскажи про SaaSAiMenu", lang="ru") is None
    assert match_project_carousel("расскажи про Velox", lang="ru") is None
    assert match_project_carousel("how did you design the RAG chunk overlap?", lang="en") is None
    assert match_project_carousel("skills", lang="en") is None


def test_carousel_items_have_bilingual_descriptions():
    assert len(PROJECT_CAROUSEL) == 10
    for item in PROJECT_CAROUSEL:
        assert item.description_ru
        assert item.description_en
        assert item.description_ru != item.description_en
        assert _CYRILLIC.search(item.description_ru)
        assert not _CYRILLIC.search(item.description_en)
        assert item.localized_description("ru") == item.description_ru
        assert item.localized_description("en") == item.description_en


def test_carousel_payload_picks_description_by_lang():
    ru = match_project_carousel("проекты", lang="ru")
    en = match_project_carousel("projects", lang="en")
    assert ru is not None and en is not None
    ru_by_id = {item["id"]: item for item in ru["items"]}
    en_by_id = {item["id"]: item for item in en["items"]}
    assert {item.id: item.description_ru for item in PROJECT_CAROUSEL} == {
        item_id: item["description"] for item_id, item in ru_by_id.items()
    }
    assert {item.id: item.description_en for item in PROJECT_CAROUSEL} == {
        item_id: item["description"] for item_id, item in en_by_id.items()
    }
    assert "ВЭД" in ru_by_id["amocrm"]["description"]
    assert "foreign trade / import-export" in en_by_id["amocrm"]["description"]
    assert "VED" not in en_by_id["amocrm"]["description"]
    assert "ВЭД" not in en_by_id["amocrm"]["description"]
    for ru_item, en_item in zip(ru["items"], en["items"], strict=True):
        assert ru_item["category"] == en_item["category"]
        assert ru_item["technologies"] == en_item["technologies"]
        assert not _CYRILLIC.search(ru_item["category"])
        assert not any(_CYRILLIC.search(tech) for tech in ru_item["technologies"])
