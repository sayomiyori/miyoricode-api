from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

TOKEN_MIN = 300
TOKEN_MAX = 500
TOKEN_OVERLAP = 50


def estimate_tokens(text: str) -> int:
    words = text.split()
    return int(len(words) * 1.3) if words else 0


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    heading: str


def _split_by_heading(markdown: str) -> list[tuple[str, str]]:
    lines = markdown.replace("\r\n", "\n").split("\n")
    sections: list[tuple[str, str]] = []
    heading = ""
    buf: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if buf or heading:
                sections.append((heading, "\n".join(buf).strip()))
            heading = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    if buf or heading:
        sections.append((heading, "\n".join(buf).strip()))
    return sections


def _window_words(words: list[str], source: str, heading: str) -> list[Chunk]:
    if not words:
        return []
    chunks: list[Chunk] = []
    # Convert token targets to word counts (tokens ≈ words * 1.3).
    max_words = max(1, int(TOKEN_MAX / 1.3))
    overlap_words = max(1, int(TOKEN_OVERLAP / 1.3))
    start = 0
    while start < len(words):
        end = min(len(words), start + max_words)
        piece = " ".join(words[start:end]).strip()
        if piece:
            prefix = f"{heading}\n\n" if heading else ""
            chunks.append(Chunk(text=f"{prefix}{piece}".strip(), source=source, heading=heading))
        if end >= len(words):
            break
        start = max(end - overlap_words, start + 1)
    return chunks


def chunk_markdown(markdown: str, source: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    for heading, body in _split_by_heading(markdown):
        block = body.strip()
        if not block:
            continue
        if estimate_tokens(block) <= TOKEN_MAX:
            prefix = f"{heading}\n\n" if heading else ""
            chunks.append(Chunk(text=f"{prefix}{block}".strip(), source=source, heading=heading))
            continue
        chunks.extend(_window_words(block.split(), source, heading))
    if not chunks and markdown.strip():
        chunks.extend(_window_words(markdown.split(), source, ""))
    return chunks


def load_knowledge_files(kb_dir: Path) -> list[tuple[Path, str]]:
    files = sorted(kb_dir.glob("*.md"))
    return [(path, path.read_text(encoding="utf-8")) for path in files]


def chunk_knowledge_base(kb_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path, text in load_knowledge_files(kb_dir):
        chunks.extend(chunk_markdown(text, source=path.name))
    return chunks
