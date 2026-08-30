import logging
import os


def _resolve_level(default_level: int) -> int:
    env_level = (os.getenv("LOG_LEVEL") or "").strip().upper()
    if env_level:
        mapped = getattr(logging, env_level, None)
        if isinstance(mapped, int):
            return mapped
    return default_level


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(_resolve_level(level))
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
