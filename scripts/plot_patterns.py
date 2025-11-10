# ──────────────────────────────────────────────────────────────
# MODULE: plot_patterns.py
# PURPOSE: Generate top/bottom frequency charts for PowerPlay.
# UPDATED: Sprint 2.3.4 – Adds logging, safety, and consistent style.
# ──────────────────────────────────────────────────────────────
"""
Generates comparative bar charts of the hottest and coldest
Powerball white balls based on frequency analysis results.
"""

# ──────────────────────────────────────────────────────────────
# Standard Library Imports
# ──────────────────────────────────────────────────────────────
from pathlib import Path

import matplotlib

# ──────────────────────────────────────────────────────────────
# Third-Party Imports
# ──────────────────────────────────────────────────────────────
import pandas as pd

matplotlib.use("Agg")  # Headless-safe backend
import matplotlib.pyplot as plt

# ──────────────────────────────────────────────────────────────
# Internal Imports
# ──────────────────────────────────────────────────────────────
from utils.logger import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
DATA_PATH = Path("data/analysis_patterns_extended.csv")
OUT_PATH = Path("data/patterns_top_bottom.png")


# ──────────────────────────────────────────────────────────────
# FUNCTION: run
# PURPOSE: Generate and save top/bottom frequency plots
# ──────────────────────────────────────────────────────────────
def run(top_n: int = 10) -> None:
    """
    Generate dual-panel bar charts for the top and bottom N white balls.

    Args:
        top_n (int): Number of hottest and coldest balls to display.
    """
    if not DATA_PATH.exists():
        logger.error("❌ No analysis_patterns_extended.csv found at %s", DATA_PATH)
        return

    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        logger.error("Failed to read CSV: %s", e)
        return

    if "count" not in df.columns or "white_ball" not in df.columns:
        logger.warning("Missing expected columns in %s", DATA_PATH)
        return

    # --- Extract Top and Bottom N ---
    try:
        top = df.nlargest(top_n, "count")
        bottom = df.nsmallest(top_n, "count")
    except Exception as e:
        logger.error("Data sorting error: %s", e)
        return

    # --- Create subplots ---
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle(
        "PowerPlay – White Ball Frequency Extremes", fontsize=14, fontweight="bold"
    )

    top.plot.bar(
        x="white_ball",
        y="count",
        ax=axes[0],
        color="firebrick",
        edgecolor="black",
        legend=False,
        title=f"Top {top_n} Hottest Balls",
    )
    bottom.plot.bar(
        x="white_ball",
        y="count",
        ax=axes[1],
        color="royalblue",
        edgecolor="black",
        legend=False,
        title=f"Bottom {top_n} Coldest Balls",
    )

    for ax in axes:
        ax.set_xlabel("White Ball Number")
        ax.set_ylabel("Frequency Count")
        ax.grid(alpha=0.3)
        ax.tick_params(axis="x", rotation=0)

    fig.tight_layout(rect=[0, 0, 1, 0.95])

    # --- Save output ---
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        plt.savefig(OUT_PATH, dpi=150)
        plt.close(fig)
        logger.info("✅ Saved → %s", OUT_PATH)
        print(f"✅ Saved → {OUT_PATH}")
    except Exception as e:
        logger.error("Failed to save output: %s", e)


# ──────────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run(top_n=10)
