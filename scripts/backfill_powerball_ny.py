# ──────────────────────────────────────────────────────────────
# MODULE: backfill_powerball_ny.py
# PURPOSE: Pull full historical Powerball data (2015–present)
#          from New York Open Data API — no scraping needed.
# UPDATED: Sprint 2.6 – replaces broken scraper ingestion.
# ──────────────────────────────────────────────────────────────

import json
import time
import requests
from utils.logger import get_logger
from utils.data_io import append_draw_to_csv, CSV_PATH
from utils.db_io import insert_draw, init_db

logger = get_logger(__name__)

NY_API_URL = (
    "https://data.ny.gov/resource/d6yy-54nr.json?$limit=50000&$order=draw_date ASC"
)


def normalize_record(rec):
    """
    Convert NY JSON record to PowerPlay internal dict format.
    Example fields from API:
      {
         draw_date: "2024-11-06T00:00:00.000",
         winning_numbers: "3 12 15 56 62 8",
         multiplier: "2"
      }
    """
    try:
        date = rec.get("draw_date", "").split("T")[0]

        nums = rec.get("winning_numbers", "").split()
        nums = [int(n) for n in nums]

        whites = nums[:5]
        powerball = nums[5] if len(nums) > 5 else None

        pp_raw = rec.get("multiplier")
        power_play = int(pp_raw) if pp_raw and pp_raw.isdigit() else None

        return {
            "draw_date": date,
            "white_balls": whites,
            "powerball": powerball,
            "power_play": power_play,
        }
    except Exception as e:
        logger.error("❌ Error normalizing record %s: %s", rec, e)
        return None


def run_backfill():
    """Fetch complete historical data and populate CSV + SQLite."""
    logger.info("📘 Starting historical Powerball import (NY Open Data API)")
    init_db()

    try:
        resp = requests.get(NY_API_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("❌ Failed to fetch NY Powerball API: %s", e)
        return

    logger.info("📊 Retrieved %d historical draws", len(data))

    total = 0
    for rec in data:
        norm = normalize_record(rec)
        if not norm:
            continue

        append_draw_to_csv(norm, CSV_PATH)
        insert_draw(norm)
        total += 1

        if total % 100 == 0:
            logger.info("... inserted %d records", total)

    logger.info("✅ Historical import complete — %d total draws saved", total)


if __name__ == "__main__":
    run_backfill()
