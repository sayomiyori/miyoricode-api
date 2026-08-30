from __future__ import annotations

import os

os.environ.setdefault("SKIP_RAG", "1")
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("OPENROUTER_API_KEY", "")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
