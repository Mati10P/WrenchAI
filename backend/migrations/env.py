from alembic import context
from sqlalchemy import create_engine, pool

from app.database import Base, database_url
from app import models  # noqa: F401 - register metadata


if context.is_offline_mode():
    context.configure(
        url=database_url(), target_metadata=Base.metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(database_url(), poolclass=pool.NullPool).connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
