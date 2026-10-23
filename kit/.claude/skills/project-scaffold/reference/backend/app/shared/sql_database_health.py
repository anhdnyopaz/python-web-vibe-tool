from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.shared.interfaces import IDatabaseHealth


class SqlDatabaseHealth(IDatabaseHealth):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ping(self) -> bool:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False
