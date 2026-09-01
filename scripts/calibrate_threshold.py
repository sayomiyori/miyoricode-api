"""Calibration script for MAX_TOPIC_DISTANCE threshold.

Run manually (not in CI) with:
    python scripts/calibrate_threshold.py

Purpose: find the best separating threshold between relevant and irrelevant
queries for each topic, using the real embedding model.
"""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.embeddings import Embedder
from app.rag.index import build_index
from app.rag.retriever import Retriever, is_off_topic, MAX_TOPIC_DISTANCE

embedder = Embedder(model_name="all-MiniLM-L6-v2")
embedder.load()
KB = Path(__file__).resolve().parents[1] / "app" / "rag" / "knowledge_base"
store = build_index(embedder, kb_dir=KB)
retriever = Retriever(embedder, store)

# topic -> list of (label, query, expected_on_topic)
calibration = {
    "projects": [
        ("velox-platform",   "Velox AI running coach",           True),
        ("project-tech",     "What tech stack do you use",        True),
        ("eventpipe",       "Tell me about EventPipe",           True),
        ("saasaimenu",      "Tell me about SaaSAiMenu",          True),
        ("borscht",         "how to cook borscht recipe",        False),
        ("weather",         "weather forecast crimea",            False),
        ("movie-opinion",   "what is your favorite movie",      False),
    ],
    "skills": [
        ("python-async",    "Do you know Python async",          True),
        ("tech-list",       "What technologies do you use",      True),
        ("docker",          "Can you work with Docker",          True),
        ("fastapi",         "Do you know FastAPI",               True),
        ("borscht-skill",   "borscht recipe cooking",           False),
        ("weather-skill",   "weather in simferopol",            False),
    ],
    "me": [
        ("who-are-you",     "Who are you",                      True),
        ("your-name",       "What is your name",                True),
        ("relocate",        "Are you ready to relocate",        True),
        ("location",        "Where do you live",                 True),
        ("borscht-me",      "how to cook borscht",              False),
        ("movie-me",        "best movie 2024",                  False),
    ],
    "fun": [
        ("fun-facts",       "Tell me about fun facts",          True),
        ("hobbies",         "What are your hobbies",             True),
        ("music",           "what music do you listen to",       True),
        ("borscht-fun",     "borscht recipe ingredients",        False),
    ],
    "contact": [
        ("contact-how",     "How can I contact you",            True),
        ("telegram",        "What is your Telegram",            True),
        ("email-contact",   "do you have email",                True),
        ("borscht-contact", "borscht recipe",                   False),
    ],
}


def run_calibration() -> None:
    all_relevant: list[float] = []
    all_irrelevant: list[float] = []
    total = 0
    correct = 0

    print(
        "topic       | label                 | expected | best_score | source        | off_topic | ok?"
    )
    print("-" * 95)

    for topic, pairs in calibration.items():
        for label, query, expected in pairs:
            results = retriever.retrieve_scored(query, topic=topic, top_k=8)
            total += 1
            if results:
                best = min(results, key=lambda r: r.score)
                off = is_off_topic(topic, results)
                ok = (not off) == expected
                if ok:
                    correct += 1
                if expected:
                    all_relevant.append(best.score)
                else:
                    all_irrelevant.append(best.score)
                print(
                    f"{topic:14}| {label:22}| {str(expected):9}| {best.score:.4f}   | "
                    f"{best.chunk.source:13}| {str(off):9}| {'OK' if ok else 'FAIL'}"
                )
            else:
                off = True
                ok = expected is False
                if ok:
                    correct += 1
                print(
                    f"{topic:14}| {label:22}| {str(expected):9}| N/A        | "
                    f"-             | {str(off):9}| {'OK' if ok else 'FAIL'} (no results)"
                )

    print()
    print(f"Current threshold: MAX_TOPIC_DISTANCE = {MAX_TOPIC_DISTANCE}")
    print(f"Accuracy: {correct}/{total} = {correct/total*100:.1f}%")
    print()

    if all_relevant:
        print(
            f"Relevant scores:    min={min(all_relevant):.4f}  "
            f"max={max(all_relevant):.4f}  avg={sum(all_relevant)/len(all_relevant):.4f}"
        )
    if all_irrelevant:
        print(
            f"Irrelevant scores: min={min(all_irrelevant):.4f}  "
            f"max={max(all_irrelevant):.4f}  avg={sum(all_irrelevant)/len(all_irrelevant):.4f}"
        )

    # Find best separating threshold
    if all_relevant and all_irrelevant:
        candidates = sorted(set(all_relevant + all_irrelevant))
        best_thresh = None
        best_acc = 0.0
        for t in candidates:
            tp = sum(1 for s in all_relevant if s <= t)
            tn = sum(1 for s in all_irrelevant if s > t)
            acc = (tp + tn) / (len(all_relevant) + len(all_irrelevant))
            if acc > best_acc:
                best_acc = acc
                best_thresh = t
        print()
        print(
            f"Optimal threshold (best separation): {best_thresh:.4f}  "
            f"(accuracy {best_acc*100:.1f}%)"
        )

        # Also try midpoint between max relevant and min irrelevant
        max_rel = max(all_relevant)
        min_irel = min(all_irrelevant)
        if max_rel < min_irel:
            midpoint = (max_rel + min_irel) / 2
            tp = sum(1 for s in all_relevant if s <= midpoint)
            tn = sum(1 for s in all_irrelevant if s > midpoint)
            acc = (tp + tn) / (len(all_relevant) + len(all_irrelevant))
            print(
                f"Midpoint (max_rel={max_rel:.4f} < min_irel={min_irel:.4f}): "
                f"{midpoint:.4f}  (accuracy {acc*100:.1f}%)"
            )


if __name__ == "__main__":
    run_calibration()
