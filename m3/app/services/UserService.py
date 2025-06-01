from app.schemas.user import UserCreate, UserRead
from app.services.crud.UserRepository import UserRepository
from app.services.UnitOfWork import UnitOfWork
from sqlmodel import SQLModel


class UserService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def signup(self, user_data: UserCreate) -> UserRead:
        existing = self.uow.users.get_by_email(user_data.email)
        if existing:
            raise ValueError(f"User with this email {user_data.email} already exists")

        user = self.uow.users.create(user_data)
        self.uow.commit()
        return UserRead.model_validate(user)

    def get_by_email(self, email: str) -> UserRead | None:
        user = self.uow.users.get_by_email(email)
        if user:
            return UserRead.model_validate(user)
        return None
