# ──────────────────────────────────────────────────────────────
# MODULE: fetch_powerball.py
# PURPOSE: Simulate or fetch Powerball draw data and append locally.
# UPDATED: Sprint 2.3.4 – Adds dual-mode fetch, error handling, and logging.
# ──────────────────────────────────────────────────────────────
"""
Handles Powerball draw retrieval for the PowerPlay project.
Supports two modes:
  • REAL mode – scrape live data from powerball.com
  • SIMULATED mode – generate local test draws aligned to draw days

All results are appended to `data/powerball_draws.csv` and de-duplicated
by `draw_date`. Designed for both CLI and Streamlit dashboard use.
"""

import argparse

# ──────────────────────────────────────────────────────────────
# Standard Library Imports
# ──────────────────────────────────────────────────────────────

import random
from datetime import datetime, timedelta
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Third-Party Imports
# ──────────────────────────────────────────────────────────────
import pandas as pd

# ──────────────────────────────────────────────────────────────
# Internal Imports
# ──────────────────────────────────────────────────────────────
from utils.logger import get_logger
from utils.scraper_powerball import fetch_latest_draw, fetch_previous_draws

logger = get_logger(__name__)

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "powerball_draws.csv"
DATA_DIR.mkdir(exist_ok=True)


# ──────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────────
def get_last_draw_date() -> datetime | None:
    """Return the date of the last draw in the local CSV, if present."""
    if not CSV_PATH.exists():
        return None
    try:
        df = pd.read_csv(CSV_PATH)
        if "draw_date" in df.columns and not df.empty:
            return pd.to_datetime(df["draw_date"].max())
    except Exception as e:
        logger.warning("Unable to read last draw date: %s", e)
    return None


def next_draw_date(start_date: datetime) -> datetime:
    """Return the next Monday, Wednesday, or Saturday after start_date."""
    valid_days = {0, 2, 5}  # Mon, Wed, Sat
    next_date = start_date + timedelta(days=1)
    while next_date.weekday() not in valid_days:
        next_date += timedelta(days=1)
    return next_date


def generate_fake_draws(last_date: datetime | None, count: int = 3) -> list[dict]:
    """
    Simulate Powerball draws aligned to the Mon/Wed/Sat schedule.
    Used for testing or offline development.
    """
    draws = []
    next_date = next_draw_date(last_date or datetime(2025, 1, 1))
    for _ in range(count):
        whites = sorted(random.sample(range(1, 70), 5))
        red = random.randint(1, 26)
        pp = random.choice([2, 3, 4, 5, 10])
        draws.append(
            {
                "draw_date": next_date.strftime("%Y-%m-%d"),
                "white_balls": whites,
                "powerball": red,
                "power_play": pp,
            }
        )
        next_date = next_draw_date(next_date)
    logger.info("Generated %d simulated draws", len(draws))
    return draws


def save_draws_to_csv(draws: list[dict], force: bool = False) -> None:
    """
    Append new draws to CSV, de-duplicating on draw_date.
    If --force is passed, recreates the file.
    """
    df = pd.DataFrame(draws)
    if df.empty:
        logger.warning("No draws provided to save.")
        return

    if force or not CSV_PATH.exists():
        df.sort_values("draw_date", ascending=False).to_csv(CSV_PATH, index=False)
        logger.info("Created fresh CSV with %d records", len(df))
        return

    try:
        existing = pd.read_csv(CSV_PATH)
        merged = (
            pd.concat([existing, df])
            .drop_duplicates(subset=["draw_date"], keep="last")
            .sort_values("draw_date", ascending=False)
        )
        merged.to_csv(CSV_PATH, index=False)
        logger.info("Updated CSV with %d new records", len(df))
    except Exception as e:
        logger.error("Failed to save CSV: %s", e)


# ──────────────────────────────────────────────────────────────
# ARGUMENT PARSING
# ──────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Powerball data for PowerPlay")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Fetch real Powerball draws from powerball.com (default: simulated)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of historical draws to fetch when using --real (default: 50)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite of existing CSV (developer use)",
    )
    return parser.parse_args()


# ──────────────────────────────────────────────────────────────
# MAIN LOGIC
# ──────────────────────────────────────────────────────────────
def run(args: argparse.Namespace) -> None:
    """
    Execute the fetch workflow in either REAL or SIMULATED mode.
    """
    if getattr(args, "real", False):
        # ───────────── REAL DATA MODE ─────────────
        logger.info("Running in REAL mode — fetching live draws.")
        try:
            latest = fetch_latest_draw()
            previous = fetch_previous_draws(getattr(args, "count", 50))
        except Exception as e:
            logger.error("Scraper error: %s", e)
            latest, previous = None, []

        all_draws = []
        if latest:
            all_draws.append(latest)
        if previous:
            all_draws.extend(previous)

        if not all_draws:
            logger.error("No draws fetched from remote source.")
            return

        save_draws_to_csv(all_draws, force=getattr(args, "force", False))
        logger.info("✅ Real data fetch complete (%d draws)", len(all_draws))

    else:
        # ───────────── SIMULATION MODE ─────────────
        logger.info("Running in SIMULATED mode.")
        last_date = get_last_draw_date()
        fake_draws = generate_fake_draws(last_date, count=3)
        save_draws_to_csv(fake_draws, force=getattr(args, "force", False))
        logger.info("✅ Simulation complete (%d draws added)", len(fake_draws))


# ──────────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = parse_args()
    run(args)
