from fastapi import Request
from typing import Optional, List
import json


class PredictionForm:
    def __init__(self, request: Request):
        self.request = request
        self.errors: List[str] = []
        self.model_type: str = None
        self.data: dict = None

    async def load_data(self):
        form = await self.request.form()
        self.model_type = form.get("model_type")
        self.data_str = form.get("data")

    async def is_valid(self):
        # Проверка model_type
        if self.model_type not in ["classification", "regression"]:
            self.errors.append("Invalid model type")

        # Проверка JSON
        try:
            parsed_data = json.loads(self.data_str)

            # Если введен объект с ключом "values"
            if isinstance(parsed_data, dict) and "values" in parsed_data:
                self.data = parsed_data["values"]
            # Если введен массив
            elif isinstance(parsed_data, list):
                self.data = parsed_data
            else:
                self.errors.append("Data must be an array or object with 'values' key")

            # Проверка, что все элементы - числа
            if not all(isinstance(x, (int, float)) for x in self.data):
                self.errors.append("All elements must be numbers")

            self.data = [float(x) for x in self.data]

        except json.JSONDecodeError:
            self.errors.append("Invalid JSON format")

        return not self.errors
