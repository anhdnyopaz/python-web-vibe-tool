from redis import Redis
from redis.exceptions import RedisError

from app.shared.interfaces import ICache


class RedisCache(ICache):
    def __init__(self, client: Redis) -> None:
        self._client = client

    def get(self, key: str) -> str | None:
        return self._client.get(key)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._client.set(key, value, ex=ttl_seconds)

    def delete_prefix(self, prefix: str) -> None:
        keys = list(self._client.scan_iter(match=f"{prefix}*"))
        if keys:
            self._client.delete(*keys)

    def ping(self) -> bool:
        try:
            return bool(self._client.ping())
        except RedisError:
            return False
