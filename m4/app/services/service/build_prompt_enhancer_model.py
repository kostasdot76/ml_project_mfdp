import os
import json
import pickle
from dotenv import load_dotenv

from services.service.PromptEnhancer import PromptEnhancer
from services.service.hf_api_adapters import HFAPI_Translator
from services.service.ollama_api_adapter import OllamaLLM
from schemas.promptSchemas import PromptEnhancerInput, PromptEnhancerOutput
from services.service.mlmodelService import BaseMLModel
from services.logging.logging import get_logger
from services.service.PromptInterface import ClipEmbedder

load_dotenv()

# Константы из .env
ROLE_CENTROIDS_PATH = os.getenv("ROLE_CENTROIDS_PATH")
CLUSTER_KEYWORDS_PATH = os.getenv("CLUSTER_KEYWORDS_PATH")
BRAND_DATA_PATH = os.getenv("BRAND_DATA_PATH")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
LLM_TYPE = os.getenv("LLM_TYPE", "ollama")

logger = get_logger(__name__)


def build_prompt_enhancer_model() -> BaseMLModel:
    translator = HFAPI_Translator(
        model_id="Helsinki-NLP/opus-mt-ru-en", hf_token=HF_API_TOKEN
    )
    if LLM_TYPE == "ollama":
        llm = OllamaLLM()
    else:
        raise ValueError(f"Unsupported LLM_TYPE: {LLM_TYPE}")

    # Загрузка брендбука
    with open(BRAND_DATA_PATH, "r", encoding="utf-8") as f:
        brandbook = json.load(f)

    # Загрузка словаря ключевых слов
    with open(CLUSTER_KEYWORDS_PATH, "r", encoding="utf-8") as f:
        combined_keywords = json.load(f)

    # загрузка центроидов кластеров по ролям

    with open(ROLE_CENTROIDS_PATH, "rb") as f:
        role_centroids = pickle.load(f)

    clip_embedder = ClipEmbedder(device="cpu")

    enhancer = PromptEnhancer(
        clip_device="cpu",
        cluster_keywords=combined_keywords,
        role_centroids=role_centroids,
        translator=translator,
        llm_api=llm,
        brand_data=brandbook,
        embedder=clip_embedder,
    )

    class PromptEnhancerModel(BaseMLModel):
        def __init__(self):
            super().__init__("prompt_enhancer")

        def predict(self, data: dict) -> dict:
            try:
                input_data = PromptEnhancerInput(**data)
                result = enhancer.expand_prompt(
                    input_data.prompt_ru,
                    include_color_instruction=input_data.include_color_instruction,
                    replace_colors_with_hex=input_data.replace_colors_with_hex,
                )
                return PromptEnhancerOutput(
                    enriched_prompt=result["enriched_prompt"],
                    semantic_roles=result["semantic_roles"],
                ).dict()
            except Exception as e:
                logger.exception("Ошибка в PromptEnhancerModel")
                raise RuntimeError(f"Ошибка при расширении промпта: {e}")

        # Для prompt_enhancer — парсим JSON
        def preprocess_data(self, data: str) -> dict:
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Ошибка при декодировании JSON: {e}")

    return PromptEnhancerModel()
