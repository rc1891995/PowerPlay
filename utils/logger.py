# ──────────────────────────────────────────────────────────────
# MODULE: logger.py
# PURPOSE: Centralized logging utility for PowerPlay operations.
# ──────────────────────────────────────────────────────────────

"""
Module: logger.py
Description:
    Provides a preconfigured logger for PowerPlay scripts and
    dashboard components. Logs messages to both console and
    rotating file output (logs/powerplay.log).

Functions:
    - get_logger(name="PowerPlay"): Return a configured logger.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "powerplay.log")
MAX_LOG_SIZE = 1 * 1024 * 1024  # 1 MB
BACKUP_COUNT = 3  # keep last 3 rotations

os.makedirs(LOG_DIR, exist_ok=True)


# ──────────────────────────────────────────────────────────────
# FUNCTION: get_logger
# PURPOSE: Configure and return the global PowerPlay logger
# ──────────────────────────────────────────────────────────────
def get_logger(name="PowerPlay"):
    """
    Create (or return existing) logger with console + file output.

    Args:
        name (str): Logger name for namespace identification.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # ── Console Handler ────────────────────────────────────
        console_handler = logging.StreamHandler()
        console_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_fmt)

        # ── File Handler (rotating) ────────────────────────────
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT
        )
        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_fmt)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


# ──────────────────────────────────────────────────────────────
# DEMO (if run directly)
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log = get_logger()
    log.info("PowerPlay logging system initialized.")
    log.warning("This is a sample warning.")
    log.error("This is a sample error message.")
