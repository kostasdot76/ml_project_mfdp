from sqlmodel import SQLModel, Session, create_engine
from contextlib import contextmanager
from .config import get_settings
from services.crud.UserRepository import UserRepository

engine = create_engine(
    url=get_settings().DATABASE_URL_psycopg, echo=True, pool_size=5, max_overflow=10
)


def get_session():
    with Session(engine) as session:
        yield session


def get_session2() -> Session:
    return Session(engine)


def init_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        UserRepository(session).register_admin()
        session.commit()
