import requests
from services.service.PromptInterface import LLMInterface


# class OllamaLLM(LLMInterface):
#     def __init__(
#         self, model: str = "gemma3:1b", url: str = "http://localhost:11434/api/generate"
#     ):
#         self.model = model
#         self.url = url

#     def generate(self, prompt: str) -> str:
#         response = requests.post(self.url, json={"model": self.model, "prompt": prompt})
#         response.raise_for_status()
#         result = response.json()
#         return result.get("response", "").strip()


class OllamaLLM(LLMInterface):
    def __init__(
        self, model: str = "gemma3:1b", url: str = "http://localhost:11434/api/generate"
    ):
        self.model = model
        self.url = url

    def generate(self, prompt: str) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        response = requests.post(self.url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
