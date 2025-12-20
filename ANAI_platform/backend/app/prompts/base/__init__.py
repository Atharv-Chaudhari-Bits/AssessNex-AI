"""Base prompts package - Core system and few-shot prompts"""

from .base_prompts import (
    SYSTEM_PROMPT,
    FEW_SHOT_EXAMPLES,
    CHAIN_OF_THOUGHT_PROMPT,
    CODE_IMPLEMENTATION_PROMPT,
    ESSAY_PROMPT,
)

__all__ = [
    'SYSTEM_PROMPT',
    'FEW_SHOT_EXAMPLES',
    'CHAIN_OF_THOUGHT_PROMPT',
    'CODE_IMPLEMENTATION_PROMPT',
    'ESSAY_PROMPT',
]
