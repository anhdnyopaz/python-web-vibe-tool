from abc import ABC, abstractmethod

from app.modules.user.entity import User


class IUserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> User: ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def list(self, limit: int, offset: int) -> list[User]: ...


class IUserService(ABC):
    @abstractmethod
    def register(self, email: str, full_name: str) -> User: ...

    @abstractmethod
    def get(self, user_id: int) -> User: ...

    @abstractmethod
    def list_users(self, limit: int, offset: int) -> list[User]: ...
