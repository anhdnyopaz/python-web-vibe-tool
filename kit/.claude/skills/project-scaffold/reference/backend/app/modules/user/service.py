import re

from app.modules.user.entity import (
    InvalidUserError,
    User,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.modules.user.interfaces import IUserRepository, IUserService

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_FULL_NAME_LENGTH = 100
MAX_PAGE_SIZE = 100


class UserService(IUserService):
    def __init__(self, repository: IUserRepository) -> None:
        self._repository = repository

    def register(self, email: str, full_name: str) -> User:
        normalized_email = email.strip().lower()
        normalized_name = " ".join(full_name.split())
        if not EMAIL_PATTERN.match(normalized_email):
            raise InvalidUserError("Email không hợp lệ")
        if not normalized_name:
            raise InvalidUserError("Họ tên không được để trống")
        if len(normalized_name) > MAX_FULL_NAME_LENGTH:
            raise InvalidUserError(f"Họ tên tối đa {MAX_FULL_NAME_LENGTH} ký tự")
        if self._repository.get_by_email(normalized_email) is not None:
            raise UserAlreadyExistsError(normalized_email)
        new_user = User(id=None, email=normalized_email, full_name=normalized_name)
        return self._repository.add(new_user)

    def get(self, user_id: int) -> User:
        user = self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def list_users(self, limit: int, offset: int) -> list[User]:
        safe_limit = max(1, min(limit, MAX_PAGE_SIZE))
        return self._repository.list(limit=safe_limit, offset=max(0, offset))
