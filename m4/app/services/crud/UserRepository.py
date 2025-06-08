from models.tables import User
from models.enums import UserRole
from typing import List, Optional
from decimal import Decimal
from sqlmodel import Session, select
from typing import Optional, List
from fastapi import HTTPException, status
from auth.hash_password import HashPassword
from services.logging.logging import get_logger

logging = get_logger(logger_name=__name__)

hash_password = HashPassword()


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    # Create
    def create_user(self, email: str, password: str) -> User:
        if self.get_user_by_email(email):
            raise ValueError("Пользователь с таким емейл уже существует")

        user = User(email=email, password=password)
        self.session.add(user)
        return user

    def create_admin(self, email: str, password: str) -> User:
        if self.get_user_by_email(email):
            raise ValueError("Пользователь с таким емейл уже существует")

        user = User(email=email, password=password, role=UserRole.ADMIN)
        self.session.add(user)
        return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        users = self.session.get(User, user_id)
        if users:
            return users
        return None

    def get_user_balance(self, user_id: int) -> Decimal:
        user = self.session.get(User, user_id)
        if user:
            return user.balance
        return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        user = self.session.exec(statement).first()
        if user:
            return user
        return None

    def get_all_users(self) -> List[User]:
        statement = select(User)
        return self.session.exec(statement).all()

    def update_user(self, user: User, **fields) -> User:
        # Обновляем поля
        for field, value in fields.items():
            if hasattr(user, field):
                setattr(user, field, value)

        # Перепривязываем к сессии, если нужно
        if user not in self.session:
            self.session.add(user)

        return user

    def register_user(self, email: str, password: str):
        user_exist = self.get_user_by_email(email)
        if user_exist:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with email provided exists already.",
            )

        hashed_password = hash_password.create_hash(password)
        self.create_user(email, hashed_password)

    def register_admin(self):
        email = "admin@example.com"
        password = "admin123"
        user_exist = self.get_user_by_email(email)
        if user_exist:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Admin already exists."
            )

        hashed_password = hash_password.create_hash(password)
        self.create_admin(email, hashed_password)

    # Delete
    def delete_user(self, user: User) -> None:
        self.session.delete(user)
