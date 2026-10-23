from app.modules.user.service import UserService
from app.usecases.user.interfaces import RegisterUserInput
from app.usecases.user.mappers import USERS_CACHE_PREFIX
from app.usecases.user.register_user import RegisterUserUseCase
from tests.fakes.fake_cache import FakeCache


def test_register_returns_output_and_clears_list_cache(user_service: UserService,
                                                       cache: FakeCache) -> None:
    cache.set(f"{USERS_CACHE_PREFIX}20:0", "[]", ttl_seconds=30)
    cache.set("other:key", "keep", ttl_seconds=30)
    usecase = RegisterUserUseCase(user_service=user_service, cache=cache)

    output = usecase.execute(RegisterUserInput(email="an@example.com", full_name="An"))

    assert output.id == 1
    assert output.email == "an@example.com"
    assert list(cache.store) == ["other:key"]
