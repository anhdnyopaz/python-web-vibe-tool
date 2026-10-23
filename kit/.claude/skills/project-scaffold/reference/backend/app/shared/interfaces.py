"""Interface (port) hạ tầng dùng chung cho usecase/service. Implementation nằm ở file riêng."""
from abc import ABC, abstractmethod


class ICache(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None: ...

    @abstractmethod
    def set(self, key: str, value: str, ttl_seconds: int) -> None: ...

    @abstractmethod
    def delete_prefix(self, prefix: str) -> None: ...

    @abstractmethod
    def ping(self) -> bool: ...


class IDatabaseHealth(ABC):
    @abstractmethod
    def ping(self) -> bool: ...
