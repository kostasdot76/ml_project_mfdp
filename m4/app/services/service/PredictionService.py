import pika
import json
import time
from abc import ABC, abstractmethod
from models.tables import User, Prediction
from models.enums import PredictionStatus
from models.schemas import PredictionRequest, PredictionTask
from services.service.UnitOfWork import UnitOfWork
from services.service.mlmodelService import (
    RegressionModel,
    ClassificationModel,
    BaseMLModel,
)
from services.service.build_prompt_enhancer_model import build_prompt_enhancer_model
from services.service.TransactionService import DebtTransaction
from typing import Optional
from database.config import get_settings
from services.service.RabbitMQClient import RabbitMQClient
from services.logging.logging import get_logger
from pydantic import ConfigDict

logging = get_logger(logger_name=__name__)

settings = get_settings()


class PredictionService(ABC):
    def __init__(self, user: User, uow: UnitOfWork):
        self.model_config = ConfigDict(protected_namespaces=())
        self.user = user
        self.uow = uow
        self.prediction: Optional[Prediction] = None
        self.rmq_client: Optional[RabbitMQClient] = None
        self._model_type = None

    def init_rabbitmq(self):
        """Инициализация подключения к RabbitMQ"""
        self.rmq_client = RabbitMQClient()
        self.rmq_client.connect()
        # time.sleep(15)  # Ожидание инициализации RabbitMQ

    def publish_task(self, task: dict):
        """Публикация задачи в очередь"""
        if not self.rmq_client:
            raise RuntimeError("RabbitMQ client not initialized")

        self.rmq_client.channel.basic_publish(
            exchange="",
            routing_key=self.rmq_client.config.RABBITMQ_QUEUE_NAME,
            body=json.dumps(task).encode(),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def close(self):
        if self.rmq_client:
            self.rmq_client.close()
            self.rmq_client = None

    def _get_model(self) -> BaseMLModel:
        if self._model_type == "prompt_enhancer":
            return BaseMLModel("prompt_enhancer")

        if self._model_type == "regression":
            return RegressionModel(settings.MODEL_NAME)

        return ClassificationModel(settings.MODEL_NAME)

    @abstractmethod
    def _validate(self) -> bool:
        """
        логика проверки
        """
        pass

    @abstractmethod
    def _apply_changes(self) -> PredictionStatus:
        """
        логика обработки
        """
        pass

    def process(self) -> bool:
        # проверка и ставим статус если не прошла
        if not self._validate():
            self.uow.predictions.update_entity_status(
                self.prediction, PredictionStatus.cancel
            )
            return False

        try:
            status = self._apply_changes()
            self.uow.predictions.update_entity_status(self.prediction, status)
            return True
        except Exception as e:
            self.uow.predictions.update_entity_status(
                self.prediction, PredictionStatus.failed
            )
            logging.info(f"Ошибка process {str(e)}")
            raise


class CreatePrediction(PredictionService):
    """
    Заказ на услугу МЛ
    """

    def __init__(self, user: User, uow: UnitOfWork, input_data: str, model_type: str):
        super().__init__(user, uow)
        self.prediction = self.uow.predictions.create_prediction(
            user_id=user.id,
            model_type=model_type,
            input_data=input_data,
            result="",
            cost=None,
            status=PredictionStatus.waiting,
        )

        # #todo
        self._input_data = input_data
        self._model_type = model_type
        self.__model = self._get_model()
        # self.prediction: Optional[Prediction] = None

    def _validate(self) -> bool:
        # Проверка баланса и данных
        if self.user.balance < self.__model._cost:
            logging.info("Недостаточно средств")
            return False
        if not self.__model.validate_input(self._input_data):
            logging.info("некорректный формат данных")
            return False

        return True

    def _make_prediction(self) -> str:
        # логика создания прогноза
        preprocessed_data = self.__model.preprocess_data(self._input_data)
        result = self.__model.predict(preprocessed_data)
        return f"Result for {self._model_type}: {result}"

    def _apply_changes(self) -> PredictionStatus:
        # Создаем транзакцию на списание
        transaction = DebtTransaction(
            user=self.user, uow=self.uow, amount=self.__model._cost
        )

        if transaction.process():
            # выполнение прогноза
            logging.info("выполнение прогноза")
            self.uow.predictions.update_result(self.prediction, self._make_prediction())
            logging.info("прогноза выполнен")
            return PredictionStatus.ready
        else:
            logging.info("Недостаточно средств")
            raise


class CreatePredictionTask(PredictionService):
    """Создание задачи на прогнозирование"""

    def __init__(self, user: User, uow: UnitOfWork, data: PredictionRequest):
        super().__init__(user, uow)
        self._model_type = data.model_type
        self._create_prediction_record(data)

    def _create_prediction_record(self, data: PredictionRequest):
        logging.info(f"Загрузка модели")
        model = self._get_model()
        logging.info(f"Получаем стоимость модели из конфига {model._model_name}")

        self.prediction = self.uow.predictions.create_prediction(
            user_id=self.user.id,
            model_type=data.model_type,
            input_data=data.input_data,
            result="",
            cost=model._cost,
            status=PredictionStatus.waiting,
        )
        # Фиксируем изменения в БД
        self.uow.session.commit()
        self.uow.session.refresh(self.prediction)

    def _validate(self) -> bool:
        model = self._get_model()
        # Проверка баланса и что какие-то данные есть
        if self.user.balance < model._cost:
            logging.info("Недостаточно средств")
            return False
        if len(self.prediction.input_data) == 0:
            return False
        return True

    def _apply_changes(self) -> PredictionStatus:

        task = {
            "prediction_id": self.prediction.id,
            "input_data": self.prediction.input_data,  # Уже список
            "model_type": self.prediction.model_type,
        }
        logging.info(f" Отправка задачи в очередь {task}")
        # Сериализуем весь объект целиком
        self.publish_task(task)
        return PredictionStatus.processed


class UpdatePredictionTask(PredictionService):
    """Обработка прогноза через воркер"""

    def __init__(self, uow: UnitOfWork, prediction_id: int, model: BaseMLModel):
        super().__init__(None, uow)  # User не требуется для обработки
        self.prediction = self.uow.predictions.get_by_id(prediction_id)
        self._model_type = self.prediction.model_type
        self.__model = model

    def _validate(self) -> bool:
        # проверка данных по требованиям модели
        if not self.__model.validate_input(self.prediction.input_data):
            logging.info("некорректный формат данных")
            return False
        return True

    def _make_prediction(self) -> str:
        # логика создания прогноза
        preprocessed_data = self.__model.preprocess_data(self.prediction.input_data)
        result = self.__model.predict(preprocessed_data)
        return f"Result for {self._model_type}: {result}"

    def _apply_changes(self) -> PredictionStatus:
        # Создаем транзакцию на списание
        user = self.uow.users.get_user_by_id(self.prediction.user_id)
        transaction = DebtTransaction(
            user=user, uow=self.uow, amount=self.__model._cost
        )

        if transaction.process():
            # выполнение прогноза
            logging.info("выполнение прогноза")
            self.prediction.status = PredictionStatus.ready
            self.uow.predictions.update_result(self.prediction, self._make_prediction())
            logging.info("прогноза выполнен")
            return PredictionStatus.ready
        return PredictionStatus.failed
