#!/usr/bin/env python3
"""
analyze_patterns.py
Performs advanced statistical analysis on cached Powerball draws.

Usage:
    python -m scripts.analyze_patterns
"""

import pandas as pd
import numpy as np
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)
DATA_PATH = Path("data/powerball_draws.csv")
OUT_PATH = Path("data/analysis_patterns.csv")


def analyze_patterns() -> pd.DataFrame:
    """Perform frequency and variability analysis on draw history."""
    if not DATA_PATH.exists():
        logger.error("Data file not found: %s", DATA_PATH)
        raise FileNotFoundError(DATA_PATH)

    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["white_balls", "powerball"])

    # --- normalize list-like strings into real Python lists ---
    df["white_balls"] = df["white_balls"].apply(
        lambda x: [int(n) for n in str(x).strip("[]").split(",") if n.strip().isdigit()]
    )
    df["powerball"] = df["powerball"].astype(int)

    # --- flatten all whites ---
    white_flat = [n for sub in df["white_balls"] for n in sub]
    red_flat = df["powerball"].tolist()

    # --- compute frequencies ---
    white_freq = pd.Series(white_flat).value_counts().sort_index()
    red_freq = pd.Series(red_flat).value_counts().sort_index()

    # --- compute stats ---
    stats = {
        "white_mean": np.mean(white_flat),
        "white_std": np.std(white_flat),
        "red_mean": np.mean(red_flat),
        "red_std": np.std(red_flat),
    }

    # --- build results frame ---
    result_df = pd.DataFrame({
        "white_ball": white_freq.index,
        "white_count": white_freq.values,
    })
    result_df["white_pct"] = (result_df["white_count"] / len(white_flat) * 100).round(2)

    # mark top 10 hot and cold
    result_df["rank"] = result_df["white_count"].rank(ascending=False)
    result_df["hot"] = result_df["rank"] <= 10
    result_df["cold"] = result_df["rank"] > (len(result_df) - 10)

    # --- save output ---
    OUT_PATH.parent.mkdir(exist_ok=True)
    result_df.to_csv(OUT_PATH, index=False)
    logger.info("Saved pattern analysis → %s", OUT_PATH)

    logger.info(
        "White mean=%.2f (σ=%.2f), Red mean=%.2f (σ=%.2f)",
        stats["white_mean"], stats["white_std"],
        stats["red_mean"], stats["red_std"]
    )
    logger.info("Top 5 hot balls: %s", result_df.nlargest(5, "white_count")["white_ball"].tolist())
    logger.info("Top 5 cold balls: %s", result_df.nsmallest(5, "white_count")["white_ball"].tolist())

    return result_df


if __name__ == "__main__":
    df_out = analyze_patterns()
    print("✅ Pattern analysis complete → data/analysis_patterns.csv")
    print(df_out.head(10))
