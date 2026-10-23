from app.shared.interfaces import ICache


class FakeCache(ICache):
    def __init__(self, healthy: bool = True) -> None:
        self.store: dict[str, str] = {}
        self.healthy = healthy

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self.store[key] = value

    def delete_prefix(self, prefix: str) -> None:
        for key in [key for key in self.store if key.startswith(prefix)]:
            del self.store[key]

    def ping(self) -> bool:
        return self.healthy
