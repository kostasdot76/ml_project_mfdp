from typing import Optional
from decimal import Decimal
from fastapi import HTTPException, status
from sqlmodel import Session, select
from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.auth.hash_password import HashPassword

# from app.services.security import HashPassword


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.session.exec(select(User).where(User.email == email)).first()

    def create_user(self, user: UserCreate, role: str = UserRole.USER) -> User:
        hashed_password = HashPassword.create_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            role=role,
            balance=Decimal("0.00"),
        )
        self.session.add(db_user)
        self.session.flush()
        return db_user

    def get_all_users(self) -> list[User]:
        return self.session.exec(select(User)).all()

    def update_user(self, user_id: int, new_data: dict):
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        for key, value in new_data.items():
            setattr(user, key, value)
        self.session.add(user)

    def delete_user(self, user_id: int):
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        self.session.delete(user)

    def increase_balance(self, user_id: int, amount: float):
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.balance += Decimal(str(amount))
        self.session.add(user)

    def decrease_balance(self, user_id: int, amount: float):
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.balance -= Decimal(str(amount))
        self.session.add(user)

    def get_balance(self, user_id: int) -> Decimal:
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user.balance
