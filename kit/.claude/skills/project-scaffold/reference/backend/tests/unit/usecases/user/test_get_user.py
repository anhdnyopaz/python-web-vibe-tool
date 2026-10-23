import pytest

from app.modules.user.entity import User, UserNotFoundError
from app.modules.user.service import UserService
from app.usecases.user.get_user import GetUserUseCase
from app.usecases.user.mappers import to_user_output


def test_get_user_returns_output(user_service: UserService) -> None:
    created = user_service.register(email="an@example.com", full_name="An")

    output = GetUserUseCase(user_service=user_service).execute(created.id)

    assert output.email == "an@example.com"


def test_get_user_propagates_not_found(user_service: UserService) -> None:
    with pytest.raises(UserNotFoundError):
        GetUserUseCase(user_service=user_service).execute(42)


def test_mapper_rejects_unsaved_user() -> None:
    with pytest.raises(ValueError):
        to_user_output(User(id=None, email="a@b.co", full_name="A"))
