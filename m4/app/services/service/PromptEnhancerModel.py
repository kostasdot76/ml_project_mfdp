from pydantic import BaseModel
from typing import Dict
from services.service.PromptEnhancer import PromptEnhancer
from services.logging.logging import get_logger
from schemas.promptSchemas import PromptEnhancerInput, PromptEnhancerOutput
from services.service.mlmodelService import BaseMLModel

logger = get_logger(__name__)


class PromptEnhancerModel(BaseMLModel):
    def __init__(self, enhancer: PromptEnhancer):
        self._enhancer = enhancer
        self._model_name = "PromptEnhancer"
        self._cost = 5  # условно, если есть тарификация
        self._is_ready = True

    def predict(self, data: Dict[str, str]) -> Dict:
        try:
            input_data = PromptEnhancerInput(**data)
            result = self._enhancer.expand_prompt(
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
