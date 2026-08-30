from app.config import Settings
from app.guardrail.output_filter import filter_output
from app.guardrail.system_prompt import CANARY
from app.tools.structured_answers import match_structured


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


def test_structured_match_projects_ru():
    match = match_structured("расскажи о проектах")
    assert match is not None
    assert match.source_file == "projects.md"
    assert "PLACEHOLDER" in match.content


def test_structured_match_ignores_freeform():
    assert match_structured("how did you design the RAG chunk overlap?") is None
