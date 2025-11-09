# ──────────────────────────────────────────────────────────────
# MODULE: fetch_powerball.py
# PURPOSE: Simulate or fetch Powerball draw data and append locally.
# ──────────────────────────────────────────────────────────────

"""
Module: fetch_powerball.py
Description:
    Handles Powerball draw retrieval for the PowerPlay project.
    Currently operates in local-only mode using simulated draws
    aligned to the Powerball schedule (Mon/Wed/Sat). Future
    versions may integrate real API data sources.

Functions:
    - get_last_draw_date(): Return the last recorded draw date.
    - next_draw_date(start_date): Compute the next valid draw day.
    - generate_fake_draws(last_date, count=3): Simulate new draw data.
    - append_draws(draws): Append generated draws to CSV file.
    - run(args): Main entrypoint for CLI or dashboard triggers.
"""

import csv
import os
import pandas as pd
import random
from datetime import datetime, timedelta
from utils.logger import get_logger
import argparse
from pathlib import Path

from utils.scraper_powerball import fetch_latest_draw, fetch_previous_draws

logger = get_logger(__name__)
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CSV_PATH = DATA_DIR / "powerball_draws.csv"


# pylint: disable=redefined-outer-name

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
DATA_FILE = "data/powerball_draws.csv"


# ──────────────────────────────────────────────────────────────
# UTILITIES
# ──────────────────────────────────────────────────────────────
def get_last_draw_date():
    """
    Return the date of the last draw in the local CSV.

    Returns:
        datetime | None: The date of the last recorded draw,
        or None if the file does not exist or is empty.
    """
    if not os.path.exists(DATA_FILE):
        return None

    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            return None
        return datetime.strptime(rows[-1]["date"], "%Y-%m-%d")


def next_draw_date(start_date):
    """
    Compute the next Powerball draw date (Monday, Wednesday, Saturday).

    Args:
        start_date (datetime): The starting reference date.

    Returns:
        datetime: The next valid draw date.
    """
    valid_days = {0, 2, 5}  # Monday, Wednesday, Saturday
    next_date = start_date + timedelta(days=1)
    while next_date.weekday() not in valid_days:
        next_date += timedelta(days=1)
    return next_date


def generate_fake_draws(last_date, count=3):
    """
    Simulate new Powerball draws aligned to Mon/Wed/Sat schedule.

    Args:
        last_date (datetime | None): Date of last recorded draw (or None).
        count (int): Number of new draws to simulate.

    Returns:
        list[dict]: Simulated draw records.
    """
    draws = []
    next_date = next_draw_date(last_date or datetime(2025, 10, 26))

    for _ in range(count):
        whites = sorted(random.sample(range(1, 70), 5))
        red = random.randint(1, 26)
        draws.append(
            {
                "date": next_date.strftime("%Y-%m-%d"),
                "white_1": whites[0],
                "white_2": whites[1],
                "white_3": whites[2],
                "white_4": whites[3],
                "white_5": whites[4],
                "red": red,
            }
        )
        next_date = next_draw_date(next_date)

    return draws


def append_draws(draws):
    """
    Append new draw rows to the CSV file.

    Args:
        draws (list[dict]): List of draw dictionaries to append.
    """
    fieldnames = ["date", "white_1", "white_2", "white_3", "white_4", "white_5", "red"]
    file_exists = os.path.exists(DATA_FILE)

    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for draw in draws:
            writer.writerow(draw)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Powerball data for PowerPlay"
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Fetch real Powerball draws from powerball.com instead of simulated data.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="How many previous draws to fetch when using --real (default: 50)",
    )
    return parser.parse_args()

def save_draws_to_csv(draws: list[dict]) -> None:
    """Append or create the powerball_draws.csv file from a list of draw dicts."""
    df = pd.DataFrame(draws).drop_duplicates(subset=["draw_date"])
    if CSV_PATH.exists():
        existing = pd.read_csv(CSV_PATH)
        merged = (
            pd.concat([existing, df])
            .drop_duplicates(subset=["draw_date"])
            .sort_values(by="draw_date", ascending=False)
        )
        merged.to_csv(CSV_PATH, index=False)
        logger.info("Updated existing CSV with %d records", len(df))
    else:
        df.sort_values(by="draw_date", ascending=False).to_csv(CSV_PATH, index=False)
        logger.info("Created new CSV at %s", CSV_PATH)


# ──────────────────────────────────────────────────────────────
# MAIN ENTRYPOINT
# ──────────────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()

    if args.real:
        # --- REAL MODE: use scraper ---
        logger.info("Running in REAL mode – fetching live draws.")
        latest = fetch_latest_draw()
        previous = fetch_previous_draws(args.count)

        # combine
        all_draws = [latest] + previous if latest else previous
        if not all_draws:
            logger.error("No draws fetched from remote source.")
            return

        save_draws_to_csv(all_draws)
        logger.info("Real data fetch complete.")
    else:
        # --- EXISTING / SIMULATED MODE ---
        # keep whatever logic you had before here
        logger.info("Running in SIMULATED mode (default).")
        # e.g. call your existing simulated draw generator
        # simulated_draws = generate_fake_draws(...)
        # save_draws_to_csv(simulated_draws)
        # or just keep current behavior
        pass


if __name__ == "__main__":
    main()

