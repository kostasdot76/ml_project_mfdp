from sqlmodel import SQLModel, Field, JSON, Column
from datetime import datetime
from decimal import Decimal
from ..enums import PredictionStatus
from typing import List


class Prediction(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    model_type: str
    input_data: List[float] = Field(sa_column=Column(JSON))
    result: str
    cost: Decimal = Field(default=Decimal(0), max_digits=10, decimal_places=2)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: PredictionStatus = Field(default=PredictionStatus.waiting)
