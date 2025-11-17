# scripts/run_daily_update.py
"""
Runs the daily Powerball auto-update (NY Open Data API).
This file is triggered automatically by cron at 08:00 AST.
"""

from utils.logger import get_logger
from scripts.backfill_powerball_ny import run_full_import

logger = get_logger(__name__)


def main():
    """Entry point for the daily cron-triggered update."""
    logger.info("🔄 Daily scheduled update started (cron)")
    run_full_import()
    logger.info("✅ Daily scheduled update completed")


if __name__ == "__main__":
    main()
