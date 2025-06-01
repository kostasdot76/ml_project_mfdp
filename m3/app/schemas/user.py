from typing import Optional
from sqlmodel import SQLModel
from enum import Enum


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class UserBase(SQLModel):
    email: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    role: UserRole
    balance: float

    class Config:
        from_attributes = True
