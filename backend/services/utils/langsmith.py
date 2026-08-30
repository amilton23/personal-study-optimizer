"""Safe LangSmith tracing bootstrap for LangChain/LangGraph apps."""

from __future__ import annotations

import os
import re

import requests

from .logs import get_logger

logger = get_logger(__name__)

_LANGSMITH_DEFAULT_ENDPOINT = "https://api.smith.langchain.com"
_ALLOWED_TRACING_MODES = {"hybrid", "langsmith", "otel"}


def configure_langsmith() -> None:
    """Normalize and guard LangSmith env vars.

    This keeps LangChain tracing enabled only when configuration looks valid,
    avoiding repeated 403/500 spam during runtime.
    """
    tracing_requested = (
        _is_truthy(os.getenv("LANGSMITH_TRACING"))
        or _is_truthy(os.getenv("LANGCHAIN_TRACING_V2"))
        or _is_truthy(os.getenv("LANGSMITH_TRACING_V2"))
    )

    logger.info("Configuring LangSmith tracing...")

    # Safe default: no tracing unless explicitly requested.
    if not tracing_requested:
        logger.info("LangSmith tracing not requested. Disabling tracing env flags.")
        _force_disable_tracing_flags()
        return

    api_key = (os.getenv("LANGSMITH_API_KEY") or "").strip()
    openrouter_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    workspace_id = (
        os.getenv("LANGSMITH_WORKSPACE_ID") or os.getenv("LANGCHAIN_WORKSPACE_ID") or ""
    ).strip()

    if not api_key:
        _disable_tracing("LANGSMITH_API_KEY is missing")
        return

    if openrouter_key and api_key == openrouter_key:
        _disable_tracing(
            "LANGSMITH_API_KEY matches OPENROUTER_API_KEY. "
            "Use a dedicated LangSmith key."
        )
        return

    if not _looks_like_langsmith_key(api_key):
        _disable_tracing(
            "LANGSMITH_API_KEY format looks invalid. "
            "Expected prefixes like 'lsv2_pt_' or 'ls__'."
        )
        return

    endpoint = (
        (os.getenv("LANGSMITH_ENDPOINT") or _LANGSMITH_DEFAULT_ENDPOINT)
        .strip()
        .rstrip("/")
    )
    os.environ["LANGSMITH_ENDPOINT"] = endpoint
    os.environ["LANGCHAIN_ENDPOINT"] = endpoint

    # Keep mode valid (or unset).
    existing_mode = (os.getenv("LANGSMITH_TRACING_MODE") or "").strip().lower()
    if existing_mode and existing_mode not in _ALLOWED_TRACING_MODES:
        logger.warning(
            "Invalid LANGSMITH_TRACING_MODE=%r detected. Resetting to 'langsmith'.",
            existing_mode,
        )
        os.environ["LANGSMITH_TRACING_MODE"] = "langsmith"

    if not _preflight_langsmith(api_key=api_key, endpoint=endpoint):
        _disable_tracing("LangSmith preflight failed (auth/endpoint/service issue)")
        return

    # Keep both modern and legacy env aliases consistent.
    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGCHAIN_API_KEY"] = api_key
    if workspace_id:
        os.environ["LANGSMITH_WORKSPACE_ID"] = workspace_id
        os.environ["LANGCHAIN_WORKSPACE_ID"] = workspace_id

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGSMITH_TRACING_V2"] = "true"
    os.environ["LANGSMITH_TRACING_MODE"] = "langsmith"

    logger.info(
        "LangSmith tracing enabled (endpoint=%s, workspace_id=%s)",
        endpoint,
        "set" if workspace_id else "not-set",
    )


def _disable_tracing(reason: str) -> None:
    _force_disable_tracing_flags()
    logger.warning("LangSmith tracing disabled: %s", reason)


def _force_disable_tracing_flags() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ["LANGSMITH_TRACING_V2"] = "false"
    # Remove mode entirely when tracing is disabled to avoid tracer init warnings.
    os.environ.pop("LANGSMITH_TRACING_MODE", None)


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _looks_like_langsmith_key(value: str) -> bool:
    # Accept modern keys like lsv2_pt_<id>_<suffix> and legacy ls__* keys.
    return bool(
        re.match(r"^(lsv2_[a-z]{2}_[A-Za-z0-9_\-]+|ls__[A-Za-z0-9_\-]+)$", value)
    )


def _preflight_langsmith(api_key: str, endpoint: str) -> bool:
    """Best-effort credential/endpoint check to prevent runtime tracing spam."""
    headers = {"x-api-key": api_key}
    workspace_id = (
        os.getenv("LANGSMITH_WORKSPACE_ID") or os.getenv("LANGCHAIN_WORKSPACE_ID") or ""
    ).strip()
    if workspace_id:
        headers["X-Tenant-Id"] = workspace_id

    probes = [
        f"{endpoint}/info",
        f"{endpoint}/sessions?limit=1",
        f"{endpoint}/datasets?limit=1",
    ]

    logger.debug(
        "LangSmith preflight started (endpoint=%s, workspace=%s)",
        endpoint,
        "set" if workspace_id else "not-set",
    )

    any_read_ok = False
    for url in probes:
        try:
            resp = requests.get(url, headers=headers, timeout=6)
            logger.debug("LangSmith preflight %s -> HTTP %s", url, resp.status_code)
            if resp.status_code < 400:
                any_read_ok = True
                continue
            if resp.status_code in {401, 403}:
                logger.warning(
                    "LangSmith preflight auth failed at %s (HTTP %s)",
                    url,
                    resp.status_code,
                )
                return False
        except requests.RequestException as exc:
            logger.debug("LangSmith preflight request error at %s: %s", url, exc)
            continue

    if not any_read_ok:
        logger.warning("LangSmith preflight failed for all read probe endpoints")
        return False

    # Extra write-permission probe. We expect 2xx/4xx validation errors when key is valid,
    # but 401/403 indicates tracing uploads will fail (e.g., wrong scope/workspace).
    write_probe_url = f"{endpoint}/runs"
    try:
        resp = requests.post(
            write_probe_url,
            headers={**headers, "Content-Type": "application/json"},
            json={},
            timeout=6,
        )
        logger.debug(
            "LangSmith write preflight %s -> HTTP %s", write_probe_url, resp.status_code
        )
        if resp.status_code in {401, 403}:
            logger.warning(
                "LangSmith write preflight failed with HTTP %s. "
                "This usually means key/workspace lacks run-ingest permission.",
                resp.status_code,
            )
            return False
    except requests.RequestException as exc:
        logger.debug("LangSmith write preflight request error: %s", exc)

    return True
