"""Composition root — nơi DUY NHẤT khởi tạo implementation và ghép chúng qua interface.

Thêm usecase mới: viết hàm build_xxx() rồi đăng ký vào PROVIDERS.
"""
from collections.abc import Callable
from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.controllers import health_controller, user_controller
from app.core.cache import get_redis
from app.core.database import engine, get_session
from app.modules.user.repository import PostgresUserRepository
from app.modules.user.service import UserService
from app.shared.interfaces import ICache
from app.shared.redis_cache import RedisCache
from app.shared.sql_database_health import SqlDatabaseHealth
from app.usecases.system.check_health import CheckHealthUseCase
from app.usecases.user.get_user import GetUserUseCase
from app.usecases.user.list_users import ListUsersUseCase
from app.usecases.user.register_user import RegisterUserUseCase


def build_cache() -> ICache:
    return RedisCache(get_redis())


def build_user_service(session: Session = Depends(get_session)) -> UserService:
    return UserService(PostgresUserRepository(session))


def build_register_user(service: UserService = Depends(build_user_service),
                        cache: ICache = Depends(build_cache)) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_service=service, cache=cache)


def build_list_users(service: UserService = Depends(build_user_service),
                     cache: ICache = Depends(build_cache)) -> ListUsersUseCase:
    return ListUsersUseCase(user_service=service, cache=cache)


def build_get_user(service: UserService = Depends(build_user_service)) -> GetUserUseCase:
    return GetUserUseCase(user_service=service)


def build_check_health(cache: ICache = Depends(build_cache)) -> CheckHealthUseCase:
    return CheckHealthUseCase(database=SqlDatabaseHealth(engine), cache=cache)


# placeholder trong controller -> hàm build thật
PROVIDERS: dict[Callable[..., Any], Callable[..., Any]] = {
    health_controller.get_check_health: build_check_health,
    user_controller.get_register_user: build_register_user,
    user_controller.get_list_users: build_list_users,
    user_controller.get_get_user: build_get_user,
}
