# ──────────────────────────────────────────────────────────────
# MODULE: fetch_powerball.py
# PURPOSE: Simulate or fetch Powerball draw data and append locally.
# UPDATED: Sprint 2.5 – aligned with new scraper API (fetch_latest_draw + scrape_previous_draws)
# ──────────────────────────────────────────────────────────────

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.scraper_powerball import fetch_latest_draw, fetch_draws_from_page

logger = get_logger(__name__)

DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "powerball_draws.csv"
DATA_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────


def get_last_draw_date() -> datetime | None:
    """Return the most recent draw_date in the local CSV."""
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
    """Return the next Mon/Wed/Sat draw date after start_date."""
    valid_days = {0, 2, 5}
    d = start_date + timedelta(days=1)
    while d.weekday() not in valid_days:
        d += timedelta(days=1)
    return d


def generate_fake_draws(last_date: datetime | None, count: int = 3) -> list[dict]:
    """Simulated draws for offline development/testing."""
    draws = []
    d = next_draw_date(last_date or datetime(2024, 1, 1))

    for _ in range(count):
        whites = sorted(random.sample(range(1, 70), 5))
        red = random.randint(1, 26)
        pp = random.choice([2, 3, 4, 5, 10])

        draws.append(
            {
                "draw_date": d.strftime("%Y-%m-%d"),
                "white_balls": whites,
                "powerball": red,
                "power_play": pp,
            }
        )

        d = next_draw_date(d)

    logger.info("Generated %d simulated draws", len(draws))
    return draws


def save_draws_to_csv(draws: list[dict], force: bool = False) -> None:
    """Append or create CSV, deduplicating by draw_date."""
    df = pd.DataFrame(draws)
    if df.empty:
        logger.warning("No draws to save.")
        return

    if force or not CSV_PATH.exists():
        df.sort_values("draw_date", ascending=False).to_csv(CSV_PATH, index=False)
        logger.info("Created new CSV with %d records", len(df))
        return

    try:
        existing = pd.read_csv(CSV_PATH)
        merged = (
            pd.concat([existing, df])
            .drop_duplicates(subset=["draw_date"], keep="last")
            .sort_values("draw_date", ascending=False)
        )
        merged.to_csv(CSV_PATH, index=False)
        logger.info("CSV updated (%d draws added)", len(df))
    except Exception as e:
        logger.error("Failed to save CSV: %s", e)


# ──────────────────────────────────────────────────────────────
# ARG PARSER
# ──────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch Powerball data for PowerPlay")
    p.add_argument(
        "--real",
        action="store_true",
        help="Use real web scraping instead of simulation",
    )
    p.add_argument(
        "--count",
        type=int,
        default=50,
        help="Historical rows to fetch when using --real",
    )
    p.add_argument("--force", action="store_true", help="Overwrite existing CSV")
    return p.parse_args()


# ──────────────────────────────────────────────────────────────
# MAIN LOGIC
# ──────────────────────────────────────────────────────────────


def run(args: argparse.Namespace) -> None:
    if args.real:
        logger.info("Running in REAL mode — fetching live Powerball data")

        latest = fetch_latest_draw()
        previous = fetch_draws_from_page(1)

        all_draws = []
        if latest:
            all_draws.append(latest)
        if previous:
            all_draws.extend(previous)

        if not all_draws:
            logger.error("No remote draws received.")
            return

        save_draws_to_csv(all_draws, force=args.force)
        logger.info("Real-mode fetch complete (%d draws)", len(all_draws))
        return

    # Simulation mode
    logger.info("Running in SIMULATED mode")
    last_date = get_last_draw_date()
    fake = generate_fake_draws(last_date, count=3)
    save_draws_to_csv(fake, force=args.force)
    logger.info("Simulation complete (%d draws added)", len(fake))


# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = parse_args()
    run(args)
