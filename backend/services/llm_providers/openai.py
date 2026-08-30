"""OpenAI-family models served via OpenRouter."""

from __future__ import annotations

import os

from . import build_openrouter_chat

OPENAI_DEFAULT_MODEL = os.getenv("OPENROUTER_OPENAI_MODEL", "openai/gpt-4o-mini")


def get_openai_llm(model: str = OPENAI_DEFAULT_MODEL, temperature: float = 0):
    return build_openrouter_chat(model=model, temperature=temperature)
