"""
Centralized logging configuration for the Agent Testing Framework.

Usage in any module:
    from src.observability.log_config import get_logger
    logger = get_logger(__name__)
    logger.info("Something happened")
"""

import logging
import sys
from pathlib import Path


# ── Log format ───────────────────────────────────────────
CONSOLE_FORMAT = "%(asctime)s │ %(levelname)-7s │ %(name)-30s │ %(message)s"
CONSOLE_DATE_FORMAT = "%H:%M:%S"

_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure root logger once.
    Call this at application startup (in main.py).
    """
    global _configured
    if _configured:
        return

    root = logging.getLogger()
    root.setLevel(level)

    # ── Console handler ──────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(
        logging.Formatter(CONSOLE_FORMAT, datefmt=CONSOLE_DATE_FORMAT)
    )
    root.addHandler(console)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger.
    If logging hasn't been set up yet, sets it up with defaults.
    """
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
