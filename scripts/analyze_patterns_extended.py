#!/usr/bin/env python3
"""
analyze_patterns_extended.py
Performs Chi-Square randomness test and visualizes Powerball white-ball frequencies.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.stats import chisquare
from utils.logger import get_logger

logger = get_logger(__name__)
DATA_PATH = Path("data/powerball_draws.csv")
OUT_CSV = Path("data/analysis_patterns_extended.csv")
OUT_PNG = Path("data/pattern_histogram.png")


def run_analysis() -> pd.DataFrame:
    """Compute frequencies, run Chi-Square test, and plot histogram."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} not found")

    df = pd.read_csv(DATA_PATH)
    df["white_balls"] = df["white_balls"].apply(
        lambda x: [int(n) for n in str(x).strip("[]").split(",") if n.strip().isdigit()]
    )
    white_flat = [n for sub in df["white_balls"] for n in sub]

    # Frequency distribution
    # Full range 1–69, fill missing with 0
    freq = pd.Series(white_flat).value_counts().reindex(range(1, 70), fill_value=0)
    total_draws = len(df)
    expected = np.full(69, (total_draws * 5) / 69)

    # Chi-Square Goodness-of-Fit
    # --- ensure exact total alignment to avoid SciPy rounding error ---
    obs = freq.values.astype(float)
    exp = expected.copy().astype(float)
    exp *= obs.sum() / exp.sum()  # scale expected totals to match observed sum exactly

    chi2, p_val = chisquare(f_obs=obs, f_exp=exp)

    logger.info("χ² = %.2f, p = %.4f", chi2, p_val)
    if p_val < 0.05:
        logger.warning("❗Possible non-uniform pattern detected (p < 0.05)")
    else:
        logger.info("✅ Distribution appears uniform (p ≥ 0.05)")

    # Save CSV
    out_df = pd.DataFrame(
        {
            "white_ball": freq.index,
            "count": freq.values,
            "expected": expected,
            "deviation": freq.values - expected,
        }
    )
    out_df.to_csv(OUT_CSV, index=False)
    logger.info("Saved extended analysis → %s", OUT_CSV)

    # Plot histogram
    plt.figure(figsize=(10, 6))
    plt.bar(freq.index, freq.values, color="skyblue", edgecolor="black")
    plt.axhline(y=expected[0], color="red", linestyle="--", label="Expected (Uniform)")
    plt.title(
        f"PowerPlay – White Ball Frequency Distribution\nχ² ={chi2:.2f}, p ={p_val:.4f}"
    )
    plt.xlabel("White Ball Number (1 – 69)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_PNG)
    logger.info("Saved histogram plot → %s", OUT_PNG)

    return out_df


if __name__ == "__main__":
    df_out = run_analysis()
    print("✅ Extended pattern analysis complete → data/analysis_patterns_extended.csv")
    print(df_out.head(10))
