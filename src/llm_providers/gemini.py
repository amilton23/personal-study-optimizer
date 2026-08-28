"""Gemini-family models served via OpenRouter."""

from __future__ import annotations

import os

from . import build_openrouter_chat

GEMINI_DEFAULT_MODEL = os.getenv(
    "GEMINI_FOUNDATION_MODEL", "google/gemini-3.1-flash-lite"
)


def get_gemini_llm(model: str = GEMINI_DEFAULT_MODEL, temperature: float = 0):
    return build_openrouter_chat(model=model, temperature=temperature)
