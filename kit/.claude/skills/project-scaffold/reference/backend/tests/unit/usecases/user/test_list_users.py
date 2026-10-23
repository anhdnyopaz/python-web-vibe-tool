import json

from app.modules.user.service import UserService
from app.usecases.user.interfaces import ListUsersInput
from app.usecases.user.list_users import ListUsersUseCase
from tests.fakes.fake_cache import FakeCache


def test_list_users_reads_service_then_caches(user_service: UserService, cache: FakeCache) -> None:
    user_service.register(email="an@example.com", full_name="An")
    usecase = ListUsersUseCase(user_service=user_service, cache=cache)

    first = usecase.execute(ListUsersInput(limit=20, offset=0))

    assert [user.email for user in first] == ["an@example.com"]
    assert json.loads(cache.store["users:list:20:0"])[0]["email"] == "an@example.com"


def test_list_users_returns_cached_value_without_hitting_service(user_service: UserService,
                                                                cache: FakeCache) -> None:
    user_service.register(email="an@example.com", full_name="An")
    usecase = ListUsersUseCase(user_service=user_service, cache=cache)
    first = usecase.execute(ListUsersInput())
    user_service.register(email="binh@example.com", full_name="Binh")

    second = usecase.execute(ListUsersInput())

    assert second == first
