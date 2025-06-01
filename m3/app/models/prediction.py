from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from .enums import PredictionStatus

if TYPE_CHECKING:
    from .user import User


class PredictionBase(SQLModel):
    model_type: str
    input_data: List[float] = Field(sa_column=Column(JSON))
    result: str
    cost: Decimal = Field(default=Decimal(0), max_digits=10, decimal_places=2)
    status: PredictionStatus = Field(default=PredictionStatus.waiting)


class Prediction(PredictionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def __str__(self):
        return (
            f"Prediction(id={self.id}, model={self.model_type}, status={self.status})"
        )


class PredictionCreate(PredictionBase):
    user_id: int
