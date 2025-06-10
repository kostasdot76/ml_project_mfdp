from typing import Type, TypeVar, Generic, Any, Optional, Dict
from sqlmodel import Session, select
from datetime import datetime
from decimal import Decimal
from models.tables import Transaction, Prediction
from models.enums import TransactionStatus, PredictionStatus

T = TypeVar("T")  # Общий тип для моделей
StatusType = TypeVar("StatusType")  # Тип для статусов


class BaseRepository(Generic[T]):
    def __init__(self, session: Session, service: Type[T]):
        self.session = session
        self.service = service

    def create_entity(self, user_id: int, **kwargs: Any) -> T:
        """Базовый метод создания сущности"""
        entity = self.service(user_id=user_id, **kwargs)
        self.session.add(entity)
        return entity

    def update_entity_status(self, entity: T, status: StatusType) -> None:
        """Обновление статуса сущности"""
        entity.status = status
        self.session.merge(entity)

    def get_user_entities(self, user_id: int) -> list[T]:
        """Получение всех сущностей пользователя"""
        statement = select(self.service).where(self.service.user_id == user_id)
        return self.session.exec(statement).all()


# Реализация для транзакций
class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: Session):
        super().__init__(session=session, service=Transaction)

    def create_transaction(
        self,
        user_id: int,
        amount: float,
        type: str,
        status: str = TransactionStatus.pending,
    ) -> Transaction:
        transaction = super().create_entity(
            user_id=user_id,
            amount=amount,
            type=type,
            status=status,
            timestamp=datetime.now(),
        )
        self.session.add(transaction)
        return transaction

    def get_all_transactions(self) -> list[Transaction]:
        return self.session.exec(select(Transaction)).all()


# Реализация для прогнозов
class PredictionRepository(BaseRepository[Prediction]):
    def __init__(self, session: Session):
        super().__init__(session=session, service=Prediction)

    def create_prediction(
        self,
        user_id: int,
        model_type: str,
        input_data: str,
        result: str,
        cost: Decimal,
        status: PredictionStatus.waiting,
    ) -> Prediction:
        prediction = super().create_entity(
            user_id=user_id,
            model_type=model_type,
            input_data=input_data,
            result=result,
            cost=cost,
            status=status,
            timestamp=datetime.now(),
        )
        self.session.add(prediction)
        return prediction

    def update_result(self, service: Prediction, result: str) -> None:
        service.result = result
        self.session.merge(service)

    def get_by_id(self, prediction_id: int) -> Optional[Prediction]:
        statement = select(Prediction).where(Prediction.id == prediction_id)
        prediction = self.session.exec(statement).first()
        if prediction:
            return prediction
        return None
