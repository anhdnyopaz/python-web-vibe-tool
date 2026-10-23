import pytest

from app.modules.user.service import UserService
from tests.fakes.fake_cache import FakeCache
from tests.fakes.in_memory_user_repository import InMemoryUserRepository


@pytest.fixture
def user_repository() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def user_service(user_repository: InMemoryUserRepository) -> UserService:
    return UserService(user_repository)


@pytest.fixture
def cache() -> FakeCache:
    return FakeCache()
