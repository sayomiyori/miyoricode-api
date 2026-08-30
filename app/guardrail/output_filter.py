from app.config import Settings
from app.guardrail.heuristic_filter import declined_reply
from app.guardrail.system_prompt import LEAK_SIGNATURES


def filter_output(
    text: str,
    lang: str,
    settings: Settings,
    *,
    enforce_length: bool = True,
) -> tuple[str, bool]:
    """Return (safe_text, leaked). leaked=True means the model echoed the system prompt.

    Word/char caps apply only to free RAG replies. Structured translations of a finite
    markdown file must not be clipped with an ellipsis.
    """
    lowered = text.lower()
    for signature in LEAK_SIGNATURES:
        if signature.lower() in lowered:
            return declined_reply(lang, settings), True

    if not enforce_length:
        return text, False

    words = text.split()
    if len(words) > settings.max_reply_words:
        text = " ".join(words[: settings.max_reply_words]).rstrip() + "…"
    if len(text) > settings.max_reply_chars:
        text = text[: settings.max_reply_chars].rstrip() + "…"
    return text, False
