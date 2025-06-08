import clip
import torch
import numpy as np
from services.service.PromptInterface import EmbedderInterface
from typing import Dict, List, Optional
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
import re


class PromptEnhancer:
    def __init__(
        self,
        clip_device: str,
        cluster_keywords: Dict,
        role_centroids: Dict,
        translator,
        llm_api,
        brand_data: Dict,
        embedder,
        stopwords: set = {"the", "a", "an"},
        threshold: float = 0.2,  # порог на cosine distance
    ):
        self.device = clip_device
        self.clip_model, self.clip_preprocess = clip.load(
            "ViT-B/32", device=clip_device
        )
        self.cluster_keywords = cluster_keywords
        self.role_centroids = role_centroids
        self.translator = translator  # должен иметь .translate(text)
        self.llm_api = llm_api  # должен иметь .generate(prompt)
        self.brand_data = brand_data
        self.stopwords = stopwords or set()
        self.threshold = threshold
        self.embedder = embedder
        self.color_map = self._build_color_map()

    def match_prompt_to_roles(
        self, prompt: str, use_fallback: bool = True
    ) -> Dict[str, dict]:
        # Векторизуем промпт через CLIP
        emb = self.embedder.encode(prompt)

        results = {}

        # Для fallback
        max_score = -1
        max_role = None
        max_cluster = None

        for role, centroids in self.role_centroids.items():
            best_score = -1
            best_cluster = None

            for cluster_id, centroid in centroids.items():
                # cosine similarity: [0, 1]
                sim = cosine_similarity([emb], [centroid])[0][0]

                # обновляем best-кластер в пределах роли
                if sim > best_score:
                    best_score = sim
                    best_cluster = cluster_id

                # обновляем абсолютный максимум (для fallback)
                if sim > max_score:
                    max_score = sim
                    max_cluster = cluster_id
                    max_role = role

            if best_score >= self.threshold:
                cluster_key = f"{role}::{best_cluster}"
                results[role] = {
                    "cluster_id": best_cluster,
                    "score": best_score,
                    "keywords": self.cluster_keywords.get(cluster_key, []),
                }

        # fallback если ничего не прошло порог
        if not results and use_fallback and max_role and max_cluster:
            cluster_key = f"{max_role}::{max_cluster}"
            results[max_role] = {
                "cluster_id": max_cluster,
                "score": max_score,
                "keywords": self.cluster_keywords.get(cluster_key, []),
            }

        return results

    def format_roles_to_prompt(
        self,
        roles: Dict[str, dict],
        original_prompt_en: Optional[str] = None,
        include_color_instruction: bool = False,
    ) -> str:
        # 1. Подготовка секций по ролям
        role_sections = []
        for role_name in ["main_object", "pattern", "background", "logo"]:
            role_data = roles.get(role_name)
            if role_data and "keywords" in role_data:
                filtered = [
                    kw.strip()
                    for kw in role_data["keywords"]
                    if kw.lower() not in self.stopwords
                ]
                if filtered:
                    label = role_name.replace("_", " ").capitalize()
                    role_sections.append(
                        f"{label} description:\n" + ", ".join(filtered)
                    )

        # 2. Инструкции бренда: стиль, шрифт
        brand_lines = []
        fonts = self.brand_data.get("fonts", [])
        font = fonts[0] if fonts else "sans-serif"
        style = self.brand_data.get("style_keywords", ["minimalism"])[0]

        brand_lines.append(f"• Use the font: {font}")
        brand_lines.append(f"• Style: {style}")

        # Доп. правило по логотипу
        if self.brand_data.get("logo_rules"):
            brand_lines.append(
                "• If logo placement is not specified — use bottom right"
            )

        # 3. Инструкции по цветам (если включено)
        if include_color_instruction:
            color_lines = []
            for color_name, color_data in self.brand_data.get("colors", {}).items():
                hexval = color_data.get("hex")
                if hexval:
                    color_lines.append(f"{hexval} ({color_name})")
            if color_lines:
                brand_lines.append(
                    "• Use only these brand colors:\n" + "\n".join(color_lines)
                )

        # 4. Финальный prompt
        prompt_parts = []

        prompt_parts.append("You are an expert in branded image generation.")
        if original_prompt_en:
            prompt_parts.append(
                f'Based on the prompt: "{original_prompt_en}", and semantic clusters of visual segments from previous examples, '
                "generate a richer, more detailed prompt."
            )
        else:
            prompt_parts.append(
                "Based on the visual segmentation and brand rules, generate a detailed prompt."
            )

        if role_sections:
            prompt_parts.append(
                "Here are semantic keywords per part of the image:\n"
                + "\n".join(role_sections)
            )

        if brand_lines:
            prompt_parts.append("Brand style instructions:\n" + "\n".join(brand_lines))

        prompt_parts.append("### Output:")

        return "\n\n".join(prompt_parts)

    def generate_prompt_with_llm(self, prompt: str) -> str:
        return self.llm_api.generate(prompt)

    def _build_color_map(self) -> Dict[str, str]:
        color_map = {}
        for name, value in self.brand_data.get("colors", {}).items():
            hexval = value.get("hex")
            synonyms = value.get("synonyms", [])
            for synonym in synonyms:
                color_map[synonym.lower()] = hexval
        return color_map

    def normalize_colors_in_prompt(self, prompt_text: str) -> str:
        for name, hexval in self.color_map.items():
            prompt_text = re.sub(
                rf"\b{name}\b", hexval, prompt_text, flags=re.IGNORECASE
            )
        return prompt_text

    def expand_prompt(
        self,
        prompt_ru: str,
        include_color_instruction: bool = False,
        replace_colors_with_hex: bool = False,
    ) -> Dict:
        # 1. Перевод
        prompt_en = self.translator.translate(prompt_ru)

        # 2. Поиск ролей
        roles = self.match_prompt_to_roles(prompt_en)

        # 3. Формирование входа в LLM
        prompt_input = self.format_roles_to_prompt(
            roles,
            original_prompt_en=prompt_en,
            include_color_instruction=include_color_instruction,
        )

        # 4. Генерация промпта от LLM
        enriched = self.generate_prompt_with_llm(prompt_input)

        # 5. Замена цветов на HEX
        if replace_colors_with_hex:
            enriched = self.normalize_colors_in_prompt(enriched)

        # 6. Возврат результатов
        return {
            "translated": prompt_en,
            "enriched_prompt": enriched,
            "semantic_roles": roles,
        }
