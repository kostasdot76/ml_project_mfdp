### PredictionRepository.py — example/app/services/crud/PredictionRepository.py
from datetime import datetime
from app.models.prediction import Prediction, PredictionStatus
from .BaseRepository import BaseRepository
from sqlmodel import select


class PredictionRepository(BaseRepository[Prediction]):
    def __init__(self, session):
        super().__init__(session, Prediction)

    def create_prediction(
        self,
        user_id: int,
        model_name: str,
        input_data: str,
        status: str = PredictionStatus.PENDING,
    ) -> Prediction:
        return self.create_entity(
            user_id=user_id,
            model_name=model_name,
            input_data=input_data,
            timestamp=datetime.now(),
            status=status,
        )

    def get_all_predictions(self) -> list[Prediction]:
        return self.session.exec(select(Prediction)).all()
