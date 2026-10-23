from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.usecases.user.interfaces import (
    IGetUserUseCase,
    IListUsersUseCase,
    IRegisterUserUseCase,
    ListUsersInput,
    RegisterUserInput,
    UserOutput,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


# Placeholder — container.py gắn implementation thật, test gắn bản giả.
def get_register_user() -> IRegisterUserUseCase:
    raise NotImplementedError


def get_list_users() -> IListUsersUseCase:
    raise NotImplementedError


def get_get_user() -> IGetUserUseCase:
    raise NotImplementedError


class RegisterUserRequest(BaseModel):
    email: str = Field(max_length=255)
    full_name: str = Field(max_length=200)


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime | None

    @classmethod
    def from_output(cls, user: UserOutput) -> "UserResponse":
        return cls(id=user.id, email=user.email, full_name=user.full_name,
                   created_at=user.created_at)


class UserListResponse(BaseModel):
    items: list[UserResponse]


@router.post("", status_code=201, response_model=UserResponse)
def register_user(body: RegisterUserRequest,
                  usecase: IRegisterUserUseCase = Depends(get_register_user)) -> UserResponse:
    user = usecase.execute(RegisterUserInput(email=body.email, full_name=body.full_name))
    return UserResponse.from_output(user)


@router.get("", response_model=UserListResponse)
def list_users(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
               usecase: IListUsersUseCase = Depends(get_list_users)) -> UserListResponse:
    users = usecase.execute(ListUsersInput(limit=limit, offset=offset))
    return UserListResponse(items=[UserResponse.from_output(user) for user in users])


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, usecase: IGetUserUseCase = Depends(get_get_user)) -> UserResponse:
    return UserResponse.from_output(usecase.execute(user_id))
