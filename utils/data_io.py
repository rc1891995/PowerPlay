# utils/data_io.py
"""
Shared data input/output helpers for PowerPlay.
Handles reading draw data, counting frequencies, and saving results.
"""

import csv
from collections import Counter
from datetime import datetime
import json
import os


DATA_FILE = "data/powerball_draws.csv"


def load_draws(filepath=DATA_FILE):
    """Load Powerball draw records from CSV."""
    draws = []
    if not os.path.exists(filepath):
        print(f"⚠️  No draw file found at {filepath}")
        return draws

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            draws.append(
                {
                    "date": datetime.strptime(row["date"], "%Y-%m-%d"),
                    "whites": [
                        int(row["white_1"]),
                        int(row["white_2"]),
                        int(row["white_3"]),
                        int(row["white_4"]),
                        int(row["white_5"]),
                    ],
                    "red": int(row["red"]),
                }
            )
    return draws


def count_frequencies(draws):
    """Return frequency counters for white and red balls."""
    white_counts, red_counts = Counter(), Counter()
    for d in draws:
        white_counts.update(d["whites"])
        red_counts.update([d["red"]])
    return white_counts, red_counts


def apply_time_weighting(draws, window=0):
    """
    Apply time-based weighting to recent draws.
    More recent draws get higher weight within the specified window.
    """
    if not window or window <= 0:
        return draws

    weighted_draws = []
    total = len(draws)
    start = max(0, total - window)

    for i, d in enumerate(draws):
        if i < start:
            weight = 1
        else:
            # recent draws get progressively higher weights
            weight = 1 + (i - start + 1) / window
        d["weight"] = weight
        weighted_draws.append(d)

    print(
        f"🧮 Applied weighting to last {window} draws (most recent weight ≈ {weight:.2f})"
    )
    return weighted_draws


def save_json(data, prefix="analysis"):
    """Save dictionary data to timestamped JSON file in /data."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/{prefix}_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved {prefix} results to {output_path}")
    return output_path
