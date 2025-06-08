from models.tables import User
from services.service.UnitOfWork import UnitOfWork
from services.logging.logging import get_logger

logging = get_logger(logger_name=__name__)


class UserService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def register_user(self, email: str, password: str) -> User:
        with self.uow:
            # проверка
            if self.uow.users.get_user_by_email(email):
                # raise ValueError("Пользователь с таким емейл уже существует")
                logging.info(f"Пользователь с емейл {email} уже существует")

            # создаем пользователя
            return self.uow.users.create_user(email, password)
