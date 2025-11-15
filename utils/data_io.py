# ──────────────────────────────────────────────────────────────
# MODULE: data_io.py
# PURPOSE: Unified data handling utilities for PowerPlay
# VERSION: PowerPlay 2.6.0
# ──────────────────────────────────────────────────────────────
"""
Utility module for reading and writing PowerPlay data files.
Handles CSV, JSON, and DataFrame conversions safely for
scraped, cached, or analyzed Powerball results.
"""

import ast
import csv
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Any

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

# Global default CSV path
CSV_PATH = Path("data/powerball_draws.csv")


# ──────────────────────────────────────────────────────────────
# FUNCTION: load_draws()
# ──────────────────────────────────────────────────────────────
def load_draws(csv_path: Path = CSV_PATH) -> List[Dict[str, Any]]:
    """
    Load Powerball draw data from CSV and normalize types.
    Handles both historical and newly scraped entries.

    Args:
        csv_path (Path): Path to the Powerball draws CSV.

    Returns:
        list[dict]: normalized records with fields:
            - draw_date (str)
            - whites (list[int])
            - red (int)
            - power_play (int)
    """
    if not csv_path.exists():
        logger.warning("CSV file not found: %s", csv_path)
        return []

    df = pd.read_csv(csv_path)
    draws = []

    for _, row in df.iterrows():
        try:
            # --- Normalize white balls ---
            whites = row.get("white_balls") or row.get("whites")
            if isinstance(whites, str):
                # Handle JSON-style or bracketed string lists
                whites = [
                    int(float(x))
                    for x in whites.strip("[]").replace(" ", "").split(",")
                    if x.strip().isdigit()
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

    valid_draws = [d for d in draws if d.get("whites") and d.get("red")]
    logger.info("Loaded %d valid draws from cache (%s)", len(valid_draws), csv_path)
    return valid_draws


# ──────────────────────────────────────────────────────────────
# FUNCTION: count_frequencies()
# ──────────────────────────────────────────────────────────────
def count_frequencies(draws: List[Dict[str, Any]]) -> Tuple[Counter, Counter]:
    """
    Compute frequency counts for white and red (Powerball) numbers.

    Args:
        draws (list[dict]): Normalized draw records.

    Returns:
        tuple(Counter, Counter): (white_counts, red_counts)
    """
    white_counts, red_counts = Counter(), Counter()
    for d in draws:
        white_counts.update(d.get("whites", []))
        red_counts.update([d.get("red")])
    return white_counts, red_counts


# ──────────────────────────────────────────────────────────────
# FUNCTION: apply_time_weighting()
# ──────────────────────────────────────────────────────────────
def apply_time_weighting(draws: List[Any], window: int = 10) -> List[Dict[str, Any]]:
    """
    Apply exponential decay weighting based on draw recency.

    Args:
        draws (list[dict | str]): Draw records (from memory or CSV load)
        window (int): Decay constant; smaller = faster decay.

    Returns:
        list[dict]: Weighted draw list with new key "weight"
    """
    weighted = []
    n = len(draws)

    for i, d in enumerate(draws):
        if isinstance(d, str):
            try:
                d = ast.literal_eval(d)
            except (SyntaxError, ValueError) as e:
                logger.warning("Failed to parse legacy row safely (%s); skipping.", e)
                continue

        if not isinstance(d, dict):
            continue

        # Apply exponential decay weighting (newest draw = highest weight)
        weight = math.exp(-(n - i - 1) / max(1, window))
        d["weight"] = weight
        weighted.append(d)

    logger.info("Applied time weighting to %d draws (window=%d)", len(weighted), window)
    return weighted


# ──────────────────────────────────────────────────────────────
# FUNCTION: save_json()
# ──────────────────────────────────────────────────────────────
def save_json(data: Dict[str, Any], prefix: str = "analysis") -> str:
    """
    Save dictionary data to a timestamped JSON file in /data.

    Args:
        data (dict): Data to serialize.
        prefix (str): Output filename prefix.

    Returns:
        str: Path of the written file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("data").mkdir(exist_ok=True)
    output_path = f"data/{prefix}_{timestamp}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info("💾 Saved %s results to %s", prefix, output_path)
    print(f"💾 Saved {prefix} results to {output_path}")
    return output_path


# ──────────────────────────────────────────────────────────────
# FUNCTION: append_draw_to_csv()
# ──────────────────────────────────────────────────────────────
def append_draw_to_csv(draw: Dict[str, Any], csv_path: Path = CSV_PATH) -> None:
    """
    Append a new Powerball draw record to the CSV.

    Args:
        draw (dict): Draw record with keys:
            - draw_date (str)
            - white_balls (list[int])
            - powerball (int)
            - power_play (int | None)
        csv_path (Path): Output CSV file path.
    """
    try:
        Path(csv_path.parent).mkdir(exist_ok=True)
        file_exists = csv_path.exists()

        with csv_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["draw_date", "white_balls", "powerball", "power_play"]
            )
            if not file_exists:
                writer.writeheader()
            writer.writerow(
                {
                    "draw_date": draw.get("draw_date"),
                    "white_balls": json.dumps(draw.get("white_balls", [])),
                    "powerball": draw.get("powerball"),
                    "power_play": draw.get("power_play"),
                }
            )

        logger.info("Appended draw %s to %s", draw.get("draw_date"), csv_path)

    except Exception as e:
        logger.error("Failed to append draw to CSV: %s", e)
