from sqlmodel import SQLModel, Field, Relationship
from decimal import Decimal
from typing import List
from ..enums import UserRole

class User(SQLModel, table=True): 
    id: int = Field(default=None, primary_key=True)
    email: str 
    password: str
    balance: Decimal = Field(default=Decimal(0), max_digits=10, decimal_places=2)    
    role: UserRole = Field(default=UserRole.USER)
    transactions: List["Transaction"] = Relationship(back_populates="user")
