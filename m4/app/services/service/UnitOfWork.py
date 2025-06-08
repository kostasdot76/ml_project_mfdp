from services.crud import UserRepository, TransactionRepository, PredictionRepository
from sqlmodel import Session
from database.database import get_session, init_db, engine
from fastapi import Depends
from database.config import get_settings


class UnitOfWork:
    def __init__(self, session: Session):
        self.session = session
        self.users = UserRepository(self.session)  # Репозиторий для User
        self.transactions = TransactionRepository(
            self.session
        )  # Репозиторий для Transaction
        self.predictions = PredictionRepository(
            self.session
        )  # Репозиторий для Transaction

    def __enter__(self):
        return self  # Возвращаем сам UnitOfWork

    def __exit__(self, exc_type, *args):
        if exc_type:
            self.session.rollback()  # Откат при ошибке
        else:
            self.session.commit()  # Фиксация изменений
        self.session.close()


def get_uow(session: Session = Depends(get_session)) -> UnitOfWork:
    return UnitOfWork(session)
