from abc import ABC, abstractmethod


class LLMError(Exception):
    def __init__(self, reason: str, status_code: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def generate(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError
