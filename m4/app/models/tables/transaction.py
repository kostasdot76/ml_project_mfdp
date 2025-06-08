from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from decimal import Decimal
from ..enums import TransactionType, TransactionStatus

class Transaction(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)    
    user_id: int = Field(foreign_key="user.id")
    amount: Decimal = Field(default=Decimal(0), max_digits=10, decimal_places=2)    
    type: TransactionType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: TransactionStatus = Field(default=TransactionStatus.pending)
    user: "User" = Relationship(back_populates="transactions")