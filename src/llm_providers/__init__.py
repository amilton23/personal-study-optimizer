"""LLM factories configured for OpenRouter."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI

from ..utils.langsmith import configure_langsmith
from ..utils.logs import get_logger

load_dotenv(find_dotenv())
load_dotenv(Path(__file__).resolve().parents[2] / ".env" / ".env")

# Ensure LangSmith tracing behavior is normalized before model clients are created.
configure_langsmith()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

logger = get_logger(__name__, level=logging.DEBUG)


def build_openrouter_chat(model: str, temperature: float = 0) -> ChatOpenAI:
    """Return a ChatOpenAI client pointing to OpenRouter."""
    logger.debug(f"Building ChatOpenAI client for model: {model}")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing OPENROUTER_API_KEY. Add it to your environment or .env/.env file."
        )

    extra_headers: dict[str, Any] = {}
    referer = os.getenv("OPENROUTER_HTTP_REFERER")
    title = os.getenv("OPENROUTER_APP_TITLE")
    if referer:
        extra_headers["HTTP-Referer"] = referer
    if title:
        extra_headers["X-Title"] = title

    logger.info(f"Creating ChatOpenAI client for model: {model}")

    # OpenRouter call path only. Disable LangSmith callbacks when tracing disabled,
    # preventing background multipart ingest errors from propagating/log-spamming.
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").strip().lower() == "true"
    if not tracing_enabled:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING_V2"] = "false"

    logger.debug(
        "LLM client config | model=%s temperature=%s tracing=%s referer=%s title=%s",
        model,
        temperature,
        tracing_enabled,
        bool(referer),
        bool(title),
    )

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        default_headers=extra_headers or None,
    )
