### transaction.py
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from .enums import TransactionType, TransactionStatus

if TYPE_CHECKING:
    from .user import User


class TransactionBase(SQLModel):
    amount: Decimal = Field(
        ..., max_digits=10, decimal_places=2, description="Сумма транзакции"
    )
    type: TransactionType
    status: TransactionStatus = Field(default=TransactionStatus.pending)


class Transaction(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user: "User" = Relationship(
        back_populates="transactions", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def __str__(self):
        return f"[{self.timestamp}] {self.type} {self.amount} ({self.status})"


class TransactionCreate(TransactionBase):
    user_id: int
