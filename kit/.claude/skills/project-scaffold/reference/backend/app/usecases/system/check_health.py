from app.shared.interfaces import ICache, IDatabaseHealth
from app.usecases.system.interfaces import HealthOutput, ICheckHealthUseCase


class CheckHealthUseCase(ICheckHealthUseCase):
    def __init__(self, database: IDatabaseHealth, cache: ICache) -> None:
        self._database = database
        self._cache = cache

    def execute(self) -> HealthOutput:
        return HealthOutput(database=self._database.ping(), cache=self._cache.ping())
