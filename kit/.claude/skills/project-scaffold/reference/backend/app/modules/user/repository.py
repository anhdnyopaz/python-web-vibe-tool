from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base
from app.modules.user.entity import User
from app.modules.user.interfaces import IUserRepository


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def _to_entity(model: UserModel) -> User:
    return User(id=model.id, email=model.email, full_name=model.full_name,
                created_at=model.created_at)


class PostgresUserRepository(IUserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> User:
        model = UserModel(email=user.email, full_name=user.full_name)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def get_by_id(self, user_id: int) -> User | None:
        model = self._session.get(UserModel, user_id)
        return _to_entity(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        model = self._session.scalar(select(UserModel).where(UserModel.email == email))
        return _to_entity(model) if model else None

    def list(self, limit: int, offset: int) -> list[User]:
        query = select(UserModel).order_by(UserModel.id.desc()).limit(limit).offset(offset)
        return [_to_entity(model) for model in self._session.scalars(query)]
