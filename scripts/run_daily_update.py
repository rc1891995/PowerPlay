"""
Daily updater for PowerPlay.
Runs the NY historical import (idempotent) and logs results.
"""

import logging
import sys
from utils.logger import get_logger
from scripts.backfill_powerball_ny import run_backfill  # <-- correct function

logger = get_logger("auto_update")


def main():
    logger.info("🚀 Daily update started")

    try:
        run_backfill()  # <-- correct call
    except Exception as e:
        logger.error("❌ Daily update FAILED: %s", e)
        sys.exit(1)

    logger.info("✅ Daily update completed successfully")


if __name__ == "__main__":
    main()
