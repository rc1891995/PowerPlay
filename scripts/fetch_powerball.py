# scripts/fetch_powerball.py
"""
Fetch Powerball draw data (local-only, incremental append mode)
"""

import csv
import os
from datetime import datetime, timedelta

DATA_FILE = "data/powerball_draws.csv"


def get_last_draw_date():
    """Return the date of the last draw in the local CSV (or None)."""
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            return None
        return datetime.strptime(rows[-1]["date"], "%Y-%m-%d")


def generate_fake_draws(last_date, count=3):
    """
    Temporary stub to simulate new draws until we connect to web source.
    Creates 'count' new draws after the given date.
    """
    import random

    draws = []
    next_date = (last_date or datetime(2025, 10, 26)) + timedelta(days=2)
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
        next_date += timedelta(days=2)
    return draws


def append_draws(draws):
    """Append new draw rows to the CSV file."""
    fieldnames = ["date", "white_1", "white_2", "white_3", "white_4", "white_5", "red"]
    file_exists = os.path.exists(DATA_FILE)
    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for d in draws:
            writer.writerow(d)


def run(args):
    """Main CLI entrypoint for fetch."""
    print("📁 [Fetch] Checking for existing data...")
    last_date = get_last_draw_date()
    if last_date:
        print(f"📅 Last recorded draw: {last_date.date()}")
    else:
        print("⚙️  No existing data found — creating new dataset.")
    new_draws = generate_fake_draws(last_date)
    append_draws(new_draws)
    print(f"✅ Appended {len(new_draws)} new draw(s) to {DATA_FILE}")
