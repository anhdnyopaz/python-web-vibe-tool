from app.modules.user.entity import User
from app.usecases.user.interfaces import UserOutput

USERS_CACHE_PREFIX = "users:list:"


def to_user_output(user: User) -> UserOutput:
    if user.id is None:
        raise ValueError("User chưa được lưu nên chưa có id")
    return UserOutput(id=user.id, email=user.email, full_name=user.full_name,
                      created_at=user.created_at)
