import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

import app.modules.user.repository  # noqa: F401  (đăng ký bảng vào metadata)
from app.core.database import Base

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL",
                                   "postgresql+psycopg://app:app@db:5432/app_test")

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(engine) -> Iterator[Session]:
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()
    with engine.begin() as connection:
        tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
        connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
