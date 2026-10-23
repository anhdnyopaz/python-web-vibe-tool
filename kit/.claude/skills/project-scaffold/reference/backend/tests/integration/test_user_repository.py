import pytest
from sqlalchemy.orm import Session

from app.modules.user.entity import User
from app.modules.user.repository import PostgresUserRepository

pytestmark = pytest.mark.integration


def test_add_and_get(session: Session) -> None:
    repository = PostgresUserRepository(session)

    saved = repository.add(User(id=None, email="an@example.com", full_name="An"))

    assert saved.id is not None
    assert saved.created_at is not None
    assert repository.get_by_id(saved.id) == saved
    assert repository.get_by_email("an@example.com") == saved
    assert repository.get_by_email("missing@example.com") is None


def test_list_newest_first_with_paging(session: Session) -> None:
    repository = PostgresUserRepository(session)
    for index in range(3):
        repository.add(User(id=None, email=f"u{index}@example.com", full_name=f"U{index}"))

    page = repository.list(limit=2, offset=1)

    assert [user.email for user in page] == ["u1@example.com", "u0@example.com"]
