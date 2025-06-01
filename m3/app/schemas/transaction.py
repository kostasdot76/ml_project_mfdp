### transaction.py — example/app/schemas/transaction.py
from sqlmodel import SQLModel, Field
from decimal import Decimal
from datetime import datetime


class TransactionRead(SQLModel):
    id: int
    user_id: int
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class DepositRequest(SQLModel):
    amount: Decimal = Field(default=Decimal(0), max_digits=10, decimal_places=2)
