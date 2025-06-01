from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from .enums import UserRole
import re


if TYPE_CHECKING:
    from .transaction import Transaction


class UserBase(SQLModel):
    email: str = Field(
        ...,
        unique=True,
        index=True,
        min_length=5,
        max_length=255,
        description="Электронная почта пользователя",
    )
    password: str = Field(..., min_length=4, description="Пароль (хешированный)")


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    balance: Decimal = Field(default=Decimal(0), max_digits=10, decimal_places=2)
    role: UserRole = Field(default=UserRole.USER)
    transactions: List["Transaction"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def __str__(self) -> str:
        return f"User(id={self.id}, email={self.email})"

    def validate_email(self) -> bool:
        pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
        if not pattern.match(self.email):
            raise ValueError("Неверный формат электронной почты")
        return True

    @property
    def transaction_count(self) -> int:
        return len(self.transactions)


class UserCreate(UserBase):
    pass
