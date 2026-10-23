import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def database_url():
    url = os.environ.get("DATABASE_URL")
    if not url or not url.startswith("postgresql+psycopg://"):
        raise RuntimeError("DATABASE_URL must use postgresql+psycopg://")
    return url


def session_factory(url):
    engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    return engine, sessionmaker(engine, expire_on_commit=False)
