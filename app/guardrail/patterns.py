"""Heuristic injection patterns (RU+EN).

This list lowers the attack surface. It is not complete coverage.
Typos, encodings, and novel jailbreaks will miss. See tests/test_heuristic_filter.py
for variants that currently pass vs fail.
"""

INJECTION_PATTERNS: list[str] = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"forget\s+(all\s+)?(previous|prior|your)\s+(instructions|rules|prompt)",
    r"system\s+prompt",
    r"repeat\s+(everything|all)\s+(above|before)",
    r"reveal\s+(your\s+)?(system\s+)?(prompt|instructions)",
    r"show\s+(me\s+)?(your\s+)?(system\s+)?prompt",
    r"print\s+(your\s+)?(system\s+)?(prompt|instructions)",
    r"you\s+are\s+now",
    r"developer\s+mode",
    r"jailbreak",
    r"\bDAN\b",
    r"override\s+(your\s+)?(safety|rules|instructions)",
    r"new\s+instructions\s*:",
    r"from\s+now\s+on\s+you\s+(will|must|are)",
    r"act\s+as\s+(if\s+)?(you\s+have\s+)?no\s+(restrictions|limits|rules)",
    r"напиши\s+код\s+котор",
    r"напиши\s+скрипт\s+котор",
    r"игнорируй\s+(все\s+)?(предыдущ|прошл|вышестоящ)\w*\s+(инструкц|правил)",
    r"игнорируй\s+инструкции",
    r"покажи\s+(свой\s+)?(системн\w*\s+)?промпт",
    r"раскрой\s+(свой\s+)?(системн\w*|промпт|инструкц)",
    r"выведи\s+(системн\w*\s+)?(промпт|инструкции)",
    r"повтори\s+(всё|все)\s+(что\s+)?выше",
    r"забудь\s+(все\s+)?(инструкции|правила|промпт)",
    r"режим\s+разработчика",
    r"обход\s+(защит|фильтр)",
]
