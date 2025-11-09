# ──────────────────────────────────────────────────────────────
# MODULE: data_io.py
# PURPOSE: Unified data handling utilities for PowerPlay
# VERSION: PowerPlay 2.3.3
# ──────────────────────────────────────────────────────────────
"""
Utility module for reading and writing PowerPlay data files.
Handles CSV, JSON, and DataFrame conversions safely for
scraped, cached, or analyzed Powerball results.
"""

import os
import csv
import json
import math
from pathlib import Path
from datetime import datetime
from collections import Counter
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

DATA_FILE = "data/powerball_draws.csv"


# ──────────────────────────────────────────────────────────────
# FUNCTION: load_draws()
# ──────────────────────────────────────────────────────────────
def load_draws():
    """
    Load Powerball draw data from CSV and normalize types.
    Handles both historical and newly scraped entries.

    Returns:
        list[dict]: normalized records with fields:
            - draw_date (str)
            - whites (list[int])
            - red (int)
            - power_play (int)
    """
    csv_path = Path(DATA_FILE)
    if not csv_path.exists():
        logger.warning("CSV file not found: %s", csv_path)
        return []

    df = pd.read_csv(csv_path)
    draws = []

    for _, row in df.iterrows():
        try:
            # --- Normalize white balls (from string to list[int]) ---
            whites = row.get("white_balls") or row.get("whites")
            if isinstance(whites, str):
                whites = [
                    int(float(x)) for x in whites.strip("[]").split(",") if x.strip()
                ]
            elif isinstance(whites, list):
                whites = [int(x) for x in whites]
            else:
                continue

            # --- Normalize red ball ---
            red_raw = row.get("powerball") or row.get("red")
            if pd.isna(red_raw) or red_raw == "":
                continue
            red = int(float(red_raw))

            # --- Normalize Power Play multiplier ---
            pp_raw = row.get("power_play") or 1
            try:
                pp = int(float(pp_raw))
            except Exception:
                pp = 1

            # --- Construct normalized record ---
            draws.append(
                {
                    "draw_date": str(row.get("draw_date")),
                    "whites": whites,
                    "red": red,
                    "power_play": pp,
                }
            )

        except Exception as e:
            logger.warning("Skipping malformed row: %s", e)

    # --- Sanity check ---
    valid_draws = [d for d in draws if d.get("whites") and d.get("red")]
    logger.info("Loaded %d valid draws from cache", len(valid_draws))
    return valid_draws


# ──────────────────────────────────────────────────────────────
# FUNCTION: count_frequencies()
# ──────────────────────────────────────────────────────────────
def count_frequencies(draws):
    """Return frequency counters for white and red balls."""
    white_counts, red_counts = Counter(), Counter()
    for d in draws:
        white_counts.update(d["whites"])
        red_counts.update([d["red"]])
    return white_counts, red_counts


# ──────────────────────────────────────────────────────────────
# FUNCTION: apply_time_weighting()
# ──────────────────────────────────────────────────────────────
def apply_time_weighting(draws, window: int = 10):
    """
    Apply exponential decay weighting based on draw recency.
    Ensures safe handling whether draws are dicts or string rows.

    Args:
        draws (list[dict|str]): Draw records (from memory or CSV load).
        window (int): Rolling window size.

    Returns:
        list[dict]: Weighted draws list.
    """
    weighted = []
    n = len(draws)

    for i, d in enumerate(draws):
        # Ensure record is a dict
        if isinstance(d, str):
            try:
                d = eval(d)  # fallback for legacy JSON-style rows
            except Exception:
                continue

        if not isinstance(d, dict):
            continue

        weight = math.exp(-(n - i - 1) / max(1, window))
        d["weight"] = weight
        weighted.append(d)

    return weighted


# ──────────────────────────────────────────────────────────────
# FUNCTION: save_json()
# ──────────────────────────────────────────────────────────────
def save_json(data, prefix="analysis"):
    """Save dictionary data to timestamped JSON file in /data."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/{prefix}_{timestamp}.json"

    Path("data").mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"💾 Saved {prefix} results to {output_path}")
    return output_path
