import pytest

from app.shared.interfaces import IDatabaseHealth
from app.usecases.system.check_health import CheckHealthUseCase
from tests.fakes.fake_cache import FakeCache


class FakeDatabaseHealth(IDatabaseHealth):
    def __init__(self, healthy: bool) -> None:
        self.healthy = healthy

    def ping(self) -> bool:
        return self.healthy


@pytest.mark.parametrize(("database", "cache", "healthy"),
                         [(True, True, True), (False, True, False), (True, False, False)])
def test_check_health_combines_dependencies(database: bool, cache: bool, healthy: bool) -> None:
    usecase = CheckHealthUseCase(database=FakeDatabaseHealth(database), cache=FakeCache(cache))

    result = usecase.execute()

    assert (result.database, result.cache, result.healthy) == (database, cache, healthy)
