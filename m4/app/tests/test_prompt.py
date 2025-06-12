import json
import pickle
from pathlib import Path

from services.service.PromptEnhancer import PromptEnhancer
from schemas.promptSchemas import PromptInput, PromptOutput
from services.service.PromptInterface import (
    TranslatorInterface,
    LLMInterface,
    ClipEmbedder,
)


# 🔧 Заглушки
class DummyTranslator(TranslatorInterface):
    def translate(self, text: str) -> str:
        print(f"[Translate] {text}")
        return text.lower()


class DummyLLM(LLMInterface):
    def generate(self, prompt: str) -> str:
        print(f"[LLM Input]\n{prompt}")
        return f"Generated prompt based on: {prompt[:50]}..."


# 📂 Загрузка данных
cluster_keywords = json.load(open("combined_cluster_keywords.json"))
role_centroids = pickle.load(open("role_centroids.pkl", "rb"))
brand_data = json.load(open("ast_brand_data_v1_1_eng.json"))

# ⚙️ Инициализация
embedder = ClipEmbedder(device="cpu")
enhancer = PromptEnhancer(
    clip_device="cpu",
    cluster_keywords=cluster_keywords,
    role_centroids=role_centroids,
    translator=DummyTranslator(),
    llm_api=DummyLLM(),
    brand_data=brand_data,
    stopwords={"the", "a", "an"},
)

# 🧪 Ввод
test_input = PromptInput(prompt_ru="сумка с логотипом на фоне узора")
result = enhancer.expand_prompt(test_input.prompt_ru)
output = PromptOutput(**result)

# 📤 Результат
print(output.json(indent=2))
