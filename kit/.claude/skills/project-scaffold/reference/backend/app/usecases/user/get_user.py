from app.modules.user.interfaces import IUserService
from app.usecases.user.interfaces import IGetUserUseCase, UserOutput
from app.usecases.user.mappers import to_user_output


class GetUserUseCase(IGetUserUseCase):
    def __init__(self, user_service: IUserService) -> None:
        self._user_service = user_service

    def execute(self, user_id: int) -> UserOutput:
        return to_user_output(self._user_service.get(user_id))
