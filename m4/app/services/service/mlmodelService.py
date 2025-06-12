import joblib
import os
import time
from abc import ABC, abstractmethod
from typing import Dict
from services.logging.logging import get_logger

logging = get_logger(logger_name=__name__)


# пример насследования
class BaseMLModel(ABC):
    def __init__(self, model_name: str):
        self._model_name = model_name
        self._cost = 10
        self._is_ready = False
        self._model = (
            self.load_model()
            if model_name not in ["prompt_enhancer", "image_generator"]
            else None
        )

    def load_model(self):
        model_path = f"/app/{self._model_name}"
        logging.info(f"Загрузка модели {self._model_name} путь {model_path}")

        if not os.path.exists(model_path):
            logging.info(f"по пути {model_path} Модель загружена {self._model_name}")
            raise FileNotFoundError(f"Файл модели {model_path} не найден")
        try:
            model = joblib.load(model_path)
            logging.info(f"Модель загружена {self._model_name}")
            return model
        except Exception as e:
            logging.info(f"Ошибка при загрузке модели: {e}")
            raise

    def preprocess_data(self, data: Dict[str, float]) -> list:
        return [list(data.values())]

    @abstractmethod
    def predict(self, data: list) -> list:
        """Базовый метод для предсказаний"""
        pass

    def validate_input(self, data) -> bool:
        if not isinstance(data, str):
            return False
        # return all(isinstance(x, (int, float)) for x in data.values())
        return True


class BlankModel(BaseMLModel):
    """
    модель пустышка
    """

    def __init__(self, model_name):
        super().__init__(model_name)

    def predict(self, data: list) -> list:
        return data


class RegressionModel(BaseMLModel):
    """
    класс для модели со своей реализаицкй обработки, предикта и валидации
    """

    def __init__(self, model_name):
        super().__init__(model_name)

    def predict(self, data: list) -> list:
        try:
            prediction = self._model.predict(list(data))[0]
            return {"predicted_quality": prediction}
        except Exception as e:
            raise PermissionError(f"Ошибка прогноза модели: {e}")


class ClassificationModel(BaseMLModel):
    """
    класс для модели со своей реализаицкй обработки, предикта и валидации
    """

    def __init__(self, model_name):
        super().__init__(model_name)

    def predict(self, data: list) -> list:
        prediction_value = self._model.predict(list(data))[0]
        # 	3.00000	5.0000	6.00000	75% = 6.000000	max = 8.00000
        if prediction_value >= 6:
            prediction = "excellent"
        if prediction_value >= 5:
            prediction = "good"
        else:
            prediction = "there is a better one"
        return {"predicted_quality": prediction}
