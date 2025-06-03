from sqlmodel import SQLModel, Field
from decimal import Decimal


class DepositRequest(SQLModel):
    amount: Decimal = Field(default=Decimal(0), max_digits=10, decimal_places=2)
