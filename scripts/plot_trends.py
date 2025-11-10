# ──────────────────────────────────────────────────────────────
# MODULE: plot_trends.py
# PURPOSE: Generate rolling frequency trend charts for PowerPlay.
# UPDATED: Sprint 2.3.4 – Adds suffix handling, safety, and logging.
# ──────────────────────────────────────────────────────────────
"""
Plots rolling frequency trends for PowerPlay white balls.
Shows how the top N numbers change in occurrence rate across
recent draws using a configurable rolling window.
"""

import ast
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

DATA_PATH = Path("data/powerball_draws.csv")
OUT_PATH = Path("data/patterns_trend.png")


# ──────────────────────────────────────────────────────────────
# FUNCTION: run
# PURPOSE: Generate and save rolling trend plots
# ──────────────────────────────────────────────────────────────
def run(top_n: int = 5, window: int = 10, suffix: str = ""):
    """
    Create a rolling frequency trend plot of the top N white balls.

    Args:
        top_n (int): Number of most frequent white balls to display.
        window (int): Rolling window size in draws.
        suffix (str): Optional suffix for output file name (e.g., "_short").
    """
    if not DATA_PATH.exists():
        logger.error("❌ No powerball_draws.csv found at %s", DATA_PATH)
        return

    # --- Load and normalize data ---
    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        logger.error("Failed to read CSV: %s", e)
        return

    records = []
    for _, row in df.iterrows():
        raw = row.get("white_balls")
        if isinstance(raw, str):
            try:
                # Safe parse for list-like strings
                nums = ast.literal_eval(raw)
                for n in nums:
                    records.append(
                        {"draw_date": row.get("draw_date"), "white_ball": int(n)}
                    )
            except Exception:
                continue

    if not records:
        logger.warning("No valid white ball records found — skipping trend plot.")
        return

    df_long = pd.DataFrame(records)
    df_long["draw_date"] = pd.to_datetime(df_long["draw_date"], errors="coerce")
    df_long = df_long.dropna(subset=["draw_date"]).sort_values("draw_date")

    if len(df_long["draw_date"].unique()) < window:
        logger.warning(
            "Not enough draws (%d) for window size %d.", len(df_long), window
        )
        return

    # --- Compute rolling frequencies ---
    pivot = (
        df_long.groupby(["draw_date", "white_ball"])
        .size()
        .unstack(fill_value=0)
        .rolling(window=window, min_periods=1)
        .sum()
    )

    # --- Identify top N balls overall ---
    top_balls = df_long["white_ball"].value_counts().nlargest(top_n).index
    pivot = pivot[top_balls]

    # --- Plot configuration ---
    plt.figure(figsize=(10, 6))
    pivot.plot(ax=plt.gca(), linewidth=2)
    plt.title(f"Rolling {window}-Draw Frequency of Top {top_n} Balls")
    plt.xlabel("Draw Date")
    plt.ylabel("Occurrences (Rolling Sum)")
    plt.legend(title="Ball #", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # --- Save output ---
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_file = OUT_PATH.with_name(f"patterns_trend{suffix}.png")

    try:
        plt.savefig(out_file)
        plt.close()
        logger.info("✅ Saved rolling trend plot → %s", out_file)
        print(f"✅ Saved → {out_file}")
    except Exception as e:
        logger.error("Failed to save trend plot: %s", e)


# ──────────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run(top_n=5, window=10)
