from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class HealthOutput:
    database: bool
    cache: bool

    @property
    def healthy(self) -> bool:
        return self.database and self.cache


class ICheckHealthUseCase(ABC):
    @abstractmethod
    def execute(self) -> HealthOutput: ...
