import os
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import time

# Загрузка переменных окружения
load_dotenv()


class StabilityAPIGenerator:
    """Генератор изображений через Stability AI API"""

    BASE_URL = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("STABILITY_API_KEY")
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "image/*"}

    def generate(self, prompt: str, **kwargs) -> bytes:
        """
        Генерирует изображение через Stability AI API
        Возвращает bytes изображения
        """
        # Параметры по умолчанию
        params = {
            "prompt": prompt,
            "output_format": "jpeg",
            "model": "sd3",
            "mode": "text-to-image",
        }
        params.update(kwargs)

        # Создание запроса
        files = {"none": ""}  # Фиктивный параметр для POST
        data = {k: str(v) for k, v in params.items()}

        # Отправка запроса
        response = requests.post(
            self.BASE_URL, headers=self.headers, files=files, data=data
        )

        # Обработка ответа
        if response.status_code != 200:
            try:
                error_data = response.json()
                raise RuntimeError(
                    f"API Error: {error_data.get('name')} - {error_data.get('message')}"
                )
            except:
                raise RuntimeError(f"API Error {response.status_code}: {response.text}")

        return Image.open(BytesIO(response.content))


class HuggingFaceGenerator:
    """Генератор изображений через Hugging Face Inference API"""

    BASE_URL = "https://api-inference.huggingface.co/models"

    def __init__(
        self,
        model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
        api_token: str = None,
    ):
        self.api_token = api_token or os.getenv("HF_API_TOKEN")
        self.model_id = model_id or self.FREE_MODELS[0]
        self.headers = {"Authorization": f"Bearer {self.api_token}"}

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        seed: int = None,
        wait_timeout: int = 120,
    ) -> Image.Image:
        """
        Генерирует изображение через Hugging Face API
        Возвращает объект PIL.Image
        """
        # Подготовка параметров
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
            },
        }

        if seed:
            payload["parameters"]["seed"] = seed

        # Отправка запроса
        response = requests.post(
            f"{self.BASE_URL}/{self.model_id}", headers=self.headers, json=payload
        )

        # Обработка ответа
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))

        # Если модель загружается (код 503)
        elif response.status_code == 503:
            print(f"Model is loading, waiting up to {wait_timeout} seconds...")
            return self.wait_for_model(prompt, payload, wait_timeout)

        else:
            error_msg = f"API Error {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('error', 'Unknown error')}"
            except:
                error_msg += f": {response.text}"
            raise RuntimeError(error_msg)

    def wait_for_model(self, prompt: str, payload: dict, timeout: int) -> Image.Image:
        """Ожидает загрузки модели и повторяет запрос"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Проверка статуса модели
            status_response = requests.get(
                f"{self.BASE_URL}/{self.model_id}/status", headers=self.headers
            )

            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("loaded"):
                    # Повторный запрос после загрузки
                    response = requests.post(
                        f"{self.BASE_URL}/{self.model_id}",
                        headers=self.headers,
                        json=payload,
                    )
                    if response.status_code == 200:
                        return Image.open(BytesIO(response.content))

            time.sleep(5)  # Проверяем каждые 5 секунд

        raise TimeoutError("Model loading timed out")
