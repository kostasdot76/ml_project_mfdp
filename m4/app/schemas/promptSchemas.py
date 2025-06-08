from pydantic import BaseModel
from typing import List, Dict, Optional


class PromptInput(BaseModel):
    prompt_ru: str


class RoleData(BaseModel):
    cluster_id: str
    score: float
    keywords: List[str]


class PromptOutput(BaseModel):
    translated: str
    enriched_prompt: str
    semantic_roles: Dict[str, RoleData]


class PromptEnhancerInput(BaseModel):
    prompt_ru: str
    include_color_instruction: bool = True
    replace_colors_with_hex: bool = False


class PromptEnhancerOutput(BaseModel):
    enriched_prompt: str
    semantic_roles: Dict[str, dict]
