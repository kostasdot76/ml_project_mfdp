import os
import json
import pickle
from dotenv import load_dotenv
from pathlib import Path
from services.service.ImageGenerator import HuggingFaceGenerator, StabilityAPIGenerator
from services.service.mlmodelService import BaseMLModel
from schemas.promptSchemas import PromptImageInput, PromptImageOutput
from services.logging.logging import get_logger


load_dotenv()

# Константы из .env
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
IMAGE_PATH = os.getenv("IMAGE_PATH")
logger = get_logger(__name__)


def build_image_generator_model() -> BaseMLModel:

    hf_gen = HuggingFaceGenerator(
        model_id="stabilityai/stable-diffusion-xl-base-1.0", api_token=HF_API_TOKEN
    )

    class ImageGeneratorModel(BaseMLModel):
        def __init__(self):
            super().__init__("image_generator")

        def predict(self, data: dict) -> dict:

            try:
                logger.info(f"Старт генерации избражения {data}")
                input_data = PromptImageInput(**data)

                if Path("static/images").exists() > 0:
                    # image_file = f"{IMAGE_PATH}/image_order_{input_data.order_id}.jpg"
                    image_file = (
                        Path("static/images")
                        / f"image_order_{input_data.prompt_order_id}.jpg"
                    )

                    if not image_file.exists():
                        image = hf_gen.generate(
                            prompt=input_data.prompt,
                            negative_prompt=input_data.negative_prompt,
                            width=768,
                            height=768,
                            guidance_scale=8.0,
                        )

                        image.save(image_file)
                        logger.info(
                            f"Изображение успешно сгенерировано и сохранено {image_file}"
                        )
                    else:
                        logger.info(
                            f"Изображение уже было сгенерировано и сохранено {image_file}"
                        )

                    return PromptImageOutput(
                        prompt=input_data.prompt,
                        prompt_order_id=input_data.prompt_order_id,
                        image=image_file.__str__(),
                        negative_prompt=input_data.negative_prompt,
                    )
                else:
                    logger.info(f"Ошибка генерации избражения - нет папки")
                    raise RuntimeError(f"Ошибка генерации избражения -  нет папки")

            except Exception as e:
                logger.exception("Ошибка в ImageGeneratorModel")
                raise RuntimeError(f"Ошибка генерации: {e}")

        def preprocess_data(self, data: str) -> dict:
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Ошибка при декодировании JSON: {e}")

    return ImageGeneratorModel()
