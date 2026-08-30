from app.config import Settings
from app.guardrail.heuristic_filter import declined_reply
from app.guardrail.system_prompt import LEAK_SIGNATURES


def filter_output(text: str, lang: str, settings: Settings) -> tuple[str, bool]:
    """Return (safe_text, leaked). leaked=True means the model echoed the system prompt."""
    lowered = text.lower()
    for signature in LEAK_SIGNATURES:
        if signature.lower() in lowered:
            return declined_reply(lang, settings), True

    words = text.split()
    if len(words) > settings.max_reply_words:
        text = " ".join(words[: settings.max_reply_words]).rstrip() + "…"
    if len(text) > settings.max_reply_chars:
        text = text[: settings.max_reply_chars].rstrip() + "…"
    return text, False
