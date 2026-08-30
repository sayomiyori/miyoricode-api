"""Forced translations for abbreviations the model otherwise transliterates.

Add entries as new calques show up in EN replies. Only `en` is injected into
the English system prompt; Russian replies keep the source abbreviations.
"""

GLOSSARY: dict[str, dict[str, str]] = {
    "ВЭД": {"en": "foreign trade / import-export business"},
}


def glossary_instruction(lang: str) -> str:
    if lang != "en":
        return ""
    pairs = [
        f"{term} → {phrases['en']}"
        for term, phrases in GLOSSARY.items()
        if phrases.get("en")
    ]
    if not pairs:
        return ""
    return (
        "The following Russian abbreviations must be translated using these exact "
        "English phrases, never transliterated: "
        + "; ".join(pairs)
        + ". Glossary entries override the copy-proper-names rule."
    )
