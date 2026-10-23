from dataclasses import replace
from datetime import UTC, datetime

from app.modules.user.entity import User
from app.modules.user.interfaces import IUserRepository


class InMemoryUserRepository(IUserRepository):
    def __init__(self) -> None:
        self.users: dict[int, User] = {}
        self._next_id = 1

    def add(self, user: User) -> User:
        saved = replace(user, id=self._next_id, created_at=datetime.now(UTC))
        self.users[self._next_id] = saved
        self._next_id += 1
        return saved

    def get_by_id(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return next((user for user in self.users.values() if user.email == email), None)

    def list(self, limit: int, offset: int) -> list[User]:
        ordered = sorted(self.users.values(), key=lambda user: user.id or 0, reverse=True)
        return ordered[offset:offset + limit]
