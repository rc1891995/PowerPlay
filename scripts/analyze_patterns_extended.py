# ──────────────────────────────────────────────────────────────
# MODULE: analyze_patterns_extended.py
# PURPOSE: Perform Chi-Square randomness test and visualize white-ball frequencies.
# UPDATED: Sprint 2.3.3 – Added normalized chi-square alignment & structured output.
# ──────────────────────────────────────────────────────────────
"""
Performs extended Powerball pattern analysis.

Features:
    • Parses historical draw data from CSV.
    • Flattens white-ball results into frequency distribution.
    • Runs Chi-Square Goodness-of-Fit test for uniformity.
    • Saves frequency table and histogram for dashboard visualization.

Outputs:
    - data/analysis_patterns_extended.csv
    - data/pattern_histogram.png
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.stats import chisquare
from utils.logger import get_logger

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
logger = get_logger(__name__)
DATA_PATH = Path("data/powerball_draws.csv")
OUT_CSV = Path("data/analysis_patterns_extended.csv")
OUT_PNG = Path("data/pattern_histogram.png")


# ──────────────────────────────────────────────────────────────
# FUNCTION: run_analysis()
# ──────────────────────────────────────────────────────────────
def run_analysis() -> pd.DataFrame:
    """
    Compute white-ball frequencies, perform a Chi-Square uniformity test,
    and visualize the results as a histogram.

    Returns:
        pd.DataFrame: white-ball counts, expected frequencies, and deviations.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} not found")

    # --- Load and normalize white-ball data ---
    df = pd.read_csv(DATA_PATH)
    df["white_balls"] = df["white_balls"].apply(
        lambda x: [int(n) for n in str(x).strip("[]").split(",") if n.strip().isdigit()]
    )
    white_flat = [n for sub in df["white_balls"] for n in sub]

    # --- Frequency distribution (1–69 inclusive) ---
    freq = pd.Series(white_flat).value_counts().reindex(range(1, 70), fill_value=0)
    total_draws = len(df)
    expected = np.full(69, (total_draws * 5) / 69)

    # --- Chi-Square Goodness-of-Fit (normalized totals) ---
    obs = freq.values.astype(float)
    exp = expected.copy().astype(float)
    exp *= obs.sum() / exp.sum()  # align totals to prevent floating-point mismatch

    chi2, p_val = chisquare(f_obs=obs, f_exp=exp)

    # --- Logging and interpretation ---
    logger.info("χ² = %.2f, p = %.4f", chi2, p_val)
    if p_val < 0.05:
        logger.warning("❗ Possible non-uniform pattern detected (p < 0.05)")
    else:
        logger.info("✅ Distribution appears uniform (p ≥ 0.05)")

    # --- Save CSV summary ---
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

    # --- Plot histogram ---
    plt.figure(figsize=(10, 6))
    plt.bar(freq.index, freq.values, color="skyblue", edgecolor="black")
    plt.axhline(
        y=expected[0],
        color="red",
        linestyle="--",
        label="Expected (Uniform Distribution)",
    )
    plt.title(
        f"PowerPlay – White Ball Frequency Distribution\nχ² = {chi2:.2f}, p = {p_val:.4f}"
    )
    plt.xlabel("White Ball Number (1–69)")
    plt.ylabel("Observed Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_PNG)
    logger.info("Saved histogram plot → %s", OUT_PNG)

    return out_df


# ──────────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df_out = run_analysis()
    print("✅ Extended pattern analysis complete → data/analysis_patterns_extended.csv")
    print(df_out.head(10))
