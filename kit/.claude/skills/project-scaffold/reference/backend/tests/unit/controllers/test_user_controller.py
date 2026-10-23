from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.controllers import user_controller
from app.main import create_app
from app.modules.user.entity import InvalidUserError, UserAlreadyExistsError, UserNotFoundError
from app.usecases.user.interfaces import (
    IGetUserUseCase,
    IListUsersUseCase,
    IRegisterUserUseCase,
    ListUsersInput,
    RegisterUserInput,
    UserOutput,
)

USER = UserOutput(id=1, email="an@example.com", full_name="An",
                  created_at=datetime(2026, 1, 1, tzinfo=UTC))


class FakeRegisterUser(IRegisterUserUseCase):
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.received: RegisterUserInput | None = None

    def execute(self, data: RegisterUserInput) -> UserOutput:
        self.received = data
        if self.error:
            raise self.error
        return USER


class FakeListUsers(IListUsersUseCase):
    def __init__(self) -> None:
        self.received: ListUsersInput | None = None

    def execute(self, data: ListUsersInput) -> list[UserOutput]:
        self.received = data
        return [USER]


class FakeGetUser(IGetUserUseCase):
    def execute(self, user_id: int) -> UserOutput:
        if user_id != USER.id:
            raise UserNotFoundError(user_id)
        return USER


@pytest.fixture
def register() -> FakeRegisterUser:
    return FakeRegisterUser()


@pytest.fixture
def list_users() -> FakeListUsers:
    return FakeListUsers()


@pytest.fixture
def client(register: FakeRegisterUser, list_users: FakeListUsers) -> TestClient:
    app = create_app(wire_dependencies=False)
    app.dependency_overrides[user_controller.get_register_user] = lambda: register
    app.dependency_overrides[user_controller.get_list_users] = lambda: list_users
    app.dependency_overrides[user_controller.get_get_user] = FakeGetUser
    return TestClient(app)


def test_register_returns_201(client: TestClient, register: FakeRegisterUser) -> None:
    response = client.post("/api/v1/users", json={"email": "an@example.com", "full_name": "An"})

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert register.received == RegisterUserInput(email="an@example.com", full_name="An")


@pytest.mark.parametrize(("error", "status", "code"), [
    (InvalidUserError("Email không hợp lệ"), 422, "validation_error"),
    (UserAlreadyExistsError("an@example.com"), 409, "conflict"),
])
def test_register_maps_domain_errors(client: TestClient, register: FakeRegisterUser,
                                     error: Exception, status: int, code: str) -> None:
    register.error = error

    response = client.post("/api/v1/users", json={"email": "x", "full_name": "An"})

    assert response.status_code == status
    assert response.json()["error"]["code"] == code


def test_list_users_passes_paging(client: TestClient, list_users: FakeListUsers) -> None:
    response = client.get("/api/v1/users?limit=5&offset=10")

    assert response.status_code == 200
    assert response.json()["items"][0]["email"] == "an@example.com"
    assert list_users.received == ListUsersInput(limit=5, offset=10)


def test_list_users_validates_limit(client: TestClient) -> None:
    assert client.get("/api/v1/users?limit=0").status_code == 422


def test_get_user_found_and_not_found(client: TestClient) -> None:
    assert client.get("/api/v1/users/1").json()["full_name"] == "An"
    assert client.get("/api/v1/users/2").status_code == 404
