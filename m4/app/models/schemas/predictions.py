from sqlmodel import SQLModel
from typing import List, Dict
from pydantic import BaseModel


class PredictionRequest(SQLModel):
    model_type: str
    input_data: str


class PredictionTask(BaseModel):
    prediction_id: int
    input_data: str
    model_type: str
