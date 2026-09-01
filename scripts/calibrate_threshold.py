"""Calibration script for MAX_TOPIC_DISTANCE threshold.

Run manually (not in CI) with:
    python scripts/calibrate_threshold.py

Purpose: find the best separating threshold between relevant and irrelevant
queries for each topic, using REAL Russian queries that match the language
of the knowledge base (all .md files are written in Russian).

IMPORTANT: This calibration is ONLY valid for lang=ru queries.
For lang=en, off-topic detection is DISABLED because the embeddings are
trained on RU text and EN queries will systematically underperform.
See retriever.py and chat.py for the lang=en guard.

The calibration data below is collected with all-MiniLM-L6-v2 embeddings.
Re-run this script after changing the embedding model or expanding the
knowledge base.
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

# All calibration queries are in RUSSIAN — matching the knowledge base language.
# Each tuple: (label, query_text, expected_on_topic)
calibration = {
    "projects": [
        # Relevant — asking about specific projects or tech stack
        ("velox-platform",      "Расскажи про Velox",                         True),
        ("tech-stack",          "Какой у тебя стек в проектах",               True),
        ("saasaimenu",          "Что такое SaaSAiMenu",                       True),
        ("ai-chaina",           "Расскажи про AI-CHAINA",                    True),
        ("eventpipe",           "Про EventPipe поподробнее",                   True),
        ("authfortress",        "Что такое AuthFortress",                    True),
        ("neuroclassifier",     "Про NeuroClassifier расскажи",               True),
        # Irrelevant — topics that have nothing to do with projects
        ("borscht",             "Как приготовить борщ",                      False),
        ("weather",             "Какая погода в Симферополе",                False),
        ("movie",               "Посоветуй фильм на вечер",                  False),
        ("recipe-okroshka",     "Рецепт окрошки",                           False),
    ],
    "skills": [
        # Relevant — asking about technologies and skills
        ("python-async",        "Ты знаешь Python async",                    True),
        ("tech-stack-skills",   "Какие технологии ты используешь",            True),
        ("docker-skills",       "Умеешь с Docker работать",                  True),
        ("fastapi-skills",      "Знаешь FastAPI",                           True),
        ("postgres-skills",     "Работаешь с PostgreSQL",                   True),
        ("ai-skills",           "Занимаешься AI/LLM интеграциями",           True),
        # Irrelevant
        ("borscht-skills",      "Рецепт борща",                            False),
        ("movie-skills",        "Лучшие фильмы 2024",                        False),
        ("weather-skills",      "Погода на неделю",                         False),
    ],
    "me": [
        # Relevant — asking about Matvey personally
        ("who-are-you",         "Кто ты такой",                             True),
        ("your-name",           "Как тебя зовут",                           True),
        ("relocate",            "Готов ли ты к переезду",                   True),
        ("location",            "Где ты живёшь",                            True),
        ("education",           "Где учился",                                True),
        # Irrelevant
        ("borscht-me",          "Рецепт борща",                            False),
        ("movie-me",            "Какой фильм посмотреть",                   False),
        ("weather-me",          "Будет ли дождь",                          False),
    ],
    "fun": [
        # Relevant — personal/hobby questions (few chunks in fun.md)
        ("hobbies",             "Чем занимаешься помимо работы",             True),
        ("music",               "Какую музыку слушаешь",                    True),
        # Irrelevant
        ("borscht-fun",         "Рецепт борща",                            False),
        ("tech-fun",            "Лучшие практики Python",                   False),
    ],
    "contact": [
        # Relevant — how to reach out
        ("how-to-contact",      "Как с тобой связаться",                    True),
        ("telegram",            "Есть телеграм",                            True),
        ("email-contact",       "Можно написать на почту",                 True),
        # Irrelevant
        ("borscht-contact",     "Рецепт борща",                            False),
        ("weather-contact",     "Погода в Крыму",                          False),
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
    print("-" * 96)

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

        # Midpoint between max relevant and min irrelevant
        max_rel = max(all_relevant)
        min_irel = min(all_irrelevant)
        if max_rel < min_irel:
            midpoint = (max_rel + min_irel) / 2
            tp = sum(1 for s in all_relevant if s <= midpoint)
            tn = sum(1 for s in all_irrelevant if s > midpoint)
            acc = (tp + tn) / (len(all_relevant) + len(all_irrelevant))
            print(
                f"Gap-based midpoint (max_rel={max_rel:.4f} < min_irel={min_irel:.4f}): "
                f"{midpoint:.4f}  (accuracy {acc*100:.1f}%)"
            )


if __name__ == "__main__":
    run_calibration()
