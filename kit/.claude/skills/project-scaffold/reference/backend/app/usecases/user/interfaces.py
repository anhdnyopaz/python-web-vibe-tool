from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserOutput:
    id: int
    email: str
    full_name: str
    created_at: datetime | None


@dataclass(frozen=True)
class RegisterUserInput:
    email: str
    full_name: str


@dataclass(frozen=True)
class ListUsersInput:
    limit: int = 20
    offset: int = 0


class IRegisterUserUseCase(ABC):
    @abstractmethod
    def execute(self, data: RegisterUserInput) -> UserOutput: ...


class IListUsersUseCase(ABC):
    @abstractmethod
    def execute(self, data: ListUsersInput) -> list[UserOutput]: ...


class IGetUserUseCase(ABC):
    @abstractmethod
    def execute(self, user_id: int) -> UserOutput: ...
