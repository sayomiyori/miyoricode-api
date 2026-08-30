from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_storage_uri: str = ""
    allowed_origins: str = "http://localhost:3000"
    rate_limit_per_minute: int = 10
    rate_limit_per_day: int = 40
    session_ttl_seconds: int = 1800
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_name: str = "session_id"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    developer_name_en: str = "Matvey"
    developer_name_ru: str = "Матвей"
    contact_placeholder: str = "[PLACEHOLDER contact — replace with real content]"
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_timeout_seconds: float = 10.0
    retrieve_k: int = 4
    session_history_limit: int = 6
    max_message_chars: int = 1500
    max_reply_words: int = 150
    max_reply_chars: int = 1200

    @property
    def origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def limiter_storage(self) -> str:
        return self.rate_limit_storage_uri or self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
