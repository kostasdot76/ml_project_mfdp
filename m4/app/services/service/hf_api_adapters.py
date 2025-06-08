import requests
from typing import Optional
from services.service.PromptInterface import TranslatorInterface, LLMInterface


class HFAPI_Translator(TranslatorInterface):
    def __init__(self, model_id: str, hf_token: str, max_retries: int = 3):
        self.url = f"https://api-inference.huggingface.co/models/{model_id}"
        self.headers = {"Authorization": f"Bearer {hf_token}"}
        self.max_retries = max_retries

    def translate(self, text: str) -> str:
        payload = {"inputs": text}
        for attempt in range(self.max_retries):
            response = requests.post(self.url, headers=self.headers, json=payload)
            if response.status_code == 503:
                result = response.json()
                wait_time = result.get("estimated_time", 5)
                time.sleep(wait_time + 1)
                continue
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list):
                if "translation_text" in result[0]:
                    return result[0]["translation_text"]
                if "generated_text" in result[0]:
                    return result[0]["generated_text"]
            return str(result)  # fallback if unexpected format
        raise RuntimeError("Translation request failed after retries.")


class HFAPI_LLM(LLMInterface):
    def __init__(
        self,
        model_id: str,
        hf_token: str,
        max_new_tokens: int = 200,
        max_retries: int = 3,
    ):
        self.url = f"https://api-inference.huggingface.co/models/{model_id}"
        self.headers = {"Authorization": f"Bearer {hf_token}"}
        self.max_new_tokens = max_new_tokens
        self.max_retries = max_retries

    def generate(self, prompt: str) -> str:
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": self.max_new_tokens,
                "do_sample": True,
                "temperature": 0.9,
                "top_p": 0.95,
            },
        }
        for attempt in range(self.max_retries):
            response = requests.post(self.url, headers=self.headers, json=payload)
            if response.status_code == 503:
                result = response.json()
                wait_time = result.get("estimated_time", 5)
                time.sleep(wait_time + 1)
                continue
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            return str(result)  # fallback for inspection
        raise RuntimeError("LLM generation failed after retries.")
