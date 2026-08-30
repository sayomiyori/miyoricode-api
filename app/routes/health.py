from fastapi import APIRouter, Request

from app.limiter import limiter
from app.session.store import SessionStore

router = APIRouter()


@router.get("/health")
@limiter.exempt
async def health(request: Request) -> dict[str, str]:
    store: SessionStore = request.app.state.session_store
    redis_ok = await store.ping()
    index_ok = getattr(request.app.state, "retriever", None) is not None
    status = "ok" if redis_ok and index_ok else "degraded"
    return {
        "status": status,
        "redis": "ok" if redis_ok else "unavailable",
        "index": "ok" if index_ok else "missing",
    }
