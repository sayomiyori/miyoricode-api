# Miyori Code API

Chat backend for **[Miyori Code](https://github.com/sayomiyori/miyoricode)** — the marble landing does not call a model itself. This service does.

A visitor asks about projects, skills, or contact. The request walks a fixed path. The model is the last stop, not the first.

```
POST /chat
  │  UUID4 session (cookie + body)
  │  10 / min · 40 / day
  │
  ├─ heuristic guardrail          → 200 fallback_declined
  ├─ structured shortcut          → Groq → OpenRouter
  └─ RAG over markdown            → Groq → OpenRouter
                                    └─ both down → contact string, still 200
```

Knowledge lives in `app/rag/knowledge_base/` markdown. The FAISS index is rebuilt on every boot (nothing is cached to disk) — restart after editing those files.

## Frontend

| | |
|---|---|
| Landing | [github.com/sayomiyori/miyoricode](https://github.com/sayomiyori/miyoricode) |
| Local UI | `http://localhost:3000` |
| This API | `http://localhost:8000` |

CORS is an allowlist (`ALLOWED_ORIGINS`), credentials on, never `*`.

## Stack

Python 3.12 · FastAPI · Redis · FAISS + `all-MiniLM-L6-v2` · Groq, then OpenRouter

## Run it

```bash
copy .env.example .env
# GROQ_API_KEY, OPENROUTER_API_KEY

docker compose up redis -d
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API + Redis in Docker (HuggingFace weights live in a named volume; the index does not):

```bash
docker compose up --build
```

| | |
|---|---|
| Health | [http://localhost:8000/health](http://localhost:8000/health) |
| Chat | `POST /chat` |

## `POST /chat`

```json
{
  "message": "Tell me about your projects",
  "lang": "en",
  "session_id": null
}
```

```json
{
  "reply": "...",
  "session_id": "uuid4",
  "source": "structured" | "rag" | "fallback_declined",
  "attachments": {
    "link": "https://…",
    "images": [{ "url": "/projects/velox/….png", "frame": "phone" | "browser", "alt": "…" }]
  } | null
}
```

`attachments` is filled only when the **user message** names a project that has media in `app/tools/project_media.py` (currently Velox / велокс). A general Projects shortcut stays `null` even though the markdown mentions Velox. Image `url` values are frontend-relative paths; this API does not host the files.

- `message`: 1–5000 characters at the request boundary. Product length is still **1500** in the heuristic — over that the chat stays **200** with `fallback_declined` so the UI can render a line, not a validation error.
- `session_id`: UUID4 from the client is kept; anything else is dropped and the server issues a new id. Same rule for the cookie. Redis keys are never arbitrary strings.
- Cookie: `HttpOnly`, `SameSite=Lax`, `Secure` off locally (`COOKIE_SECURE=false`).

Rate-limit 429s still return JSON `{ reply, session_id, source, attachments }` so the frontend can show them as a chat bubble.

## Guardrails

Heuristic regex runs **before** any provider HTTP. It reduces the jailbreak surface; it does not close it. Known misses live in `tests/test_heuristic_filter.py` (`KNOWN_MISSES`). Review brief: [`docs/ADVERSARIAL_REVIEW.md`](docs/ADVERSARIAL_REVIEW.md). Findings (pinned to a commit): [`docs/REVIEWER_FINDINGS.md`](docs/REVIEWER_FINDINGS.md).

Every response also carries `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`. CORS headers are owned by Starlette and are not overwritten.

## Tests

```bash
pytest
```

Live checks (API + Redis up): `python scripts/adversarial_check.py --all`

## Deploy

Railway reads [`railway.toml`](railway.toml) and the `Dockerfile`. The container listens on `$PORT`.

Local HTTP and production HTTPS are different cookie topologies. Do **not** flip defaults in this repo for a guess:

- Locally, UI `:3000` and API `:8000` are same-site, so `SameSite=Lax` works with credentialed `fetch`.
- When the UI is on another registrable domain (Vercel) and this API is on Railway, the request is **cross-site**. Set `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none`, HTTPS, and put the real UI origin in `ALLOWED_ORIGINS`. Flipping those defaults in git would break local HTTP.
