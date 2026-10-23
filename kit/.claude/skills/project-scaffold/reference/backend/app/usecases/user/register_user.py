from app.modules.user.interfaces import IUserService
from app.shared.interfaces import ICache
from app.usecases.user.interfaces import IRegisterUserUseCase, RegisterUserInput, UserOutput
from app.usecases.user.mappers import USERS_CACHE_PREFIX, to_user_output


class RegisterUserUseCase(IRegisterUserUseCase):
    def __init__(self, user_service: IUserService, cache: ICache) -> None:
        self._user_service = user_service
        self._cache = cache

    def execute(self, data: RegisterUserInput) -> UserOutput:
        user = self._user_service.register(email=data.email, full_name=data.full_name)
        self._cache.delete_prefix(USERS_CACHE_PREFIX)
        return to_user_output(user)
