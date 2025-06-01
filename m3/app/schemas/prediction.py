### prediction.py — example/app/schemas/prediction.py
from sqlmodel import SQLModel
from typing import Dict
from datetime import datetime
from typing import Optional


class PredictionRead(SQLModel):
    id: int
    user_id: int
    result: str
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionRequest(SQLModel):
    """
    Где используется
        routes/home.py
        services/service/PredictionService.py
    Используется в ручке FastAPI — принимается как тело запроса с параметрами модели и входными данными (input_data).

    """

    model_type: str
    input_data: Dict[str, float]
