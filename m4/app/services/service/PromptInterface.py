from abc import ABC, abstractmethod
import numpy as np
import requests


class EmbedderInterface(ABC):
    @abstractmethod
    def encode(self, text: str) -> np.ndarray: ...


class LLMInterface(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...


class TranslatorInterface(ABC):
    @abstractmethod
    def translate(self, text: str) -> str: ...


class ClipEmbedder(EmbedderInterface):
    def __init__(self, device: str = "cpu"):
        import clip

        print("Загружаем модель CLIP ViT-B/32...")
        self.model, _ = clip.load("ViT-B/32", device=device)
        self.device = device
        self.clip = clip

    def encode(self, text: str) -> np.ndarray:
        import torch

        with torch.no_grad():
            tokens = self.clip.tokenize([text]).to(self.device)
            embedding = self.model.encode_text(tokens).cpu().numpy()[0]
            # text_feat = text_feat / np.linalg.norm(text_feat) TODO
        return embedding
