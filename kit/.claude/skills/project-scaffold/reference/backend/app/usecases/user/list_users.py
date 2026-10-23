import json
from dataclasses import asdict
from datetime import datetime

from app.modules.user.interfaces import IUserService
from app.shared.interfaces import ICache
from app.usecases.user.interfaces import IListUsersUseCase, ListUsersInput, UserOutput
from app.usecases.user.mappers import USERS_CACHE_PREFIX, to_user_output

CACHE_TTL_SECONDS = 30


class ListUsersUseCase(IListUsersUseCase):
    def __init__(self, user_service: IUserService, cache: ICache) -> None:
        self._user_service = user_service
        self._cache = cache

    def execute(self, data: ListUsersInput) -> list[UserOutput]:
        cache_key = f"{USERS_CACHE_PREFIX}{data.limit}:{data.offset}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return [_from_cache(item) for item in json.loads(cached)]

        users = [to_user_output(user) for user in
                 self._user_service.list_users(limit=data.limit, offset=data.offset)]
        payload = json.dumps([asdict(user) for user in users], default=str)
        self._cache.set(cache_key, payload, ttl_seconds=CACHE_TTL_SECONDS)
        return users


def _from_cache(item: dict) -> UserOutput:
    created_at = item.get("created_at")
    return UserOutput(id=item["id"], email=item["email"], full_name=item["full_name"],
                      created_at=datetime.fromisoformat(created_at) if created_at else None)
