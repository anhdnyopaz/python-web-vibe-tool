import contextlib
import importlib
import pkgutil

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.modules
from app.core.config import get_settings
from app.core.database import Base

# Tự nạp ORM model của mọi module (app/modules/<name>/repository.py) để autogenerate thấy bảng.
for module_info in pkgutil.iter_modules(app.modules.__path__):
    with contextlib.suppress(ModuleNotFoundError):
        importlib.import_module(f"app.modules.{module_info.name}.repository")

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata,
                      literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}),
                                     prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
