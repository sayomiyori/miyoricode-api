from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings


def rate_limit_key(request: Request) -> str:
    settings = get_settings()
    session_id = request.cookies.get(settings.cookie_name)
    if session_id:
        return f"session:{session_id}"
    return get_remote_address(request)


def build_limiter() -> Limiter:
    settings = get_settings()
    return Limiter(
        key_func=rate_limit_key,
        storage_uri=settings.limiter_storage,
        headers_enabled=True,
    )


limiter = build_limiter()
