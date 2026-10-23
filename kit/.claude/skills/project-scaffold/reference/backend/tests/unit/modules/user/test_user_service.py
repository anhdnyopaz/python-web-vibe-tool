import pytest

from app.modules.user.entity import InvalidUserError, UserAlreadyExistsError, UserNotFoundError
from app.modules.user.service import MAX_PAGE_SIZE, UserService


def test_register_normalizes_email_and_name(user_service: UserService) -> None:
    user = user_service.register(email="  An@Example.COM ", full_name="  Nguyen   Van  An ")

    assert user.id == 1
    assert user.email == "an@example.com"
    assert user.full_name == "Nguyen Van An"


@pytest.mark.parametrize("email", ["", "no-at-sign", "a@b", "a b@c.com"])
def test_register_rejects_invalid_email(user_service: UserService, email: str) -> None:
    with pytest.raises(InvalidUserError):
        user_service.register(email=email, full_name="An")


def test_register_rejects_blank_name(user_service: UserService) -> None:
    with pytest.raises(InvalidUserError):
        user_service.register(email="an@example.com", full_name="   ")


def test_register_rejects_too_long_name(user_service: UserService) -> None:
    with pytest.raises(InvalidUserError):
        user_service.register(email="an@example.com", full_name="a" * 101)


def test_register_rejects_duplicate_email(user_service: UserService) -> None:
    user_service.register(email="an@example.com", full_name="An")

    with pytest.raises(UserAlreadyExistsError):
        user_service.register(email="AN@example.com", full_name="An 2")


def test_get_returns_existing_user(user_service: UserService) -> None:
    created = user_service.register(email="an@example.com", full_name="An")

    assert user_service.get(created.id) == created


def test_get_raises_when_missing(user_service: UserService) -> None:
    with pytest.raises(UserNotFoundError):
        user_service.get(999)


def test_list_users_returns_newest_first_and_clamps_paging(user_service: UserService) -> None:
    for index in range(3):
        user_service.register(email=f"u{index}@example.com", full_name=f"User {index}")

    assert [user.email for user in user_service.list_users(limit=2, offset=0)] == [
        "u2@example.com", "u1@example.com"]
    assert len(user_service.list_users(limit=0, offset=-5)) == 1
    assert len(user_service.list_users(limit=MAX_PAGE_SIZE + 50, offset=0)) == 3
