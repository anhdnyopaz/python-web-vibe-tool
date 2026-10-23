from dataclasses import dataclass
from datetime import datetime

from app.core.errors import ConflictError, NotFoundError, ValidationError


@dataclass(frozen=True)
class User:
    id: int | None
    email: str
    full_name: str
    created_at: datetime | None = None


class InvalidUserError(ValidationError):
    pass


class UserAlreadyExistsError(ConflictError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Email {email} đã được đăng ký")


class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: int) -> None:
        super().__init__(f"Không tìm thấy user #{user_id}")
