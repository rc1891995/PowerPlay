# ──────────────────────────────────────────────────────────────
# MODULE: analyze_visuals.py
# PURPOSE: Generate and save PowerPlay visual analysis charts.
# UPDATED: Sprint 2.3.4 – Adds logging, file checks, and style consistency.
# ──────────────────────────────────────────────────────────────
"""
Generates PowerPlay visualizations for white and red ball
frequencies using Matplotlib. Produces static PNG bar charts
for dashboard display and optional interactive viewing.
"""

# ──────────────────────────────────────────────────────────────
# Standard Library Imports
# ──────────────────────────────────────────────────────────────
import os
import json
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Third-Party Imports
# ──────────────────────────────────────────────────────────────
import matplotlib

matplotlib.use("Agg")  # Safe for Streamlit / headless mode
import matplotlib.pyplot as plt

# ──────────────────────────────────────────────────────────────
# Internal Imports
# ──────────────────────────────────────────────────────────────
from utils.logger import get_logger

logger = get_logger(__name__)


# ──────────────────────────────────────────────────────────────
# FUNCTION: plot_analysis
# PURPOSE: Display and save frequency charts for white & red balls
# ──────────────────────────────────────────────────────────────
def plot_analysis(json_path: str, save_plots: bool = True) -> None:
    """
    Generate bar charts for white and red ball frequencies.

    Args:
        json_path (str): Path to the analysis JSON file.
        save_plots (bool): Whether to save the generated PNG charts.

    Returns:
        None
    """
    json_file = Path(json_path)

    if not json_file.exists():
        logger.error("❌ JSON file not found: %s", json_path)
        return

    # ── Load analysis data ─────────────────────────────────────
    try:
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error("Failed to read analysis JSON: %s", e)
        return

    whites = data.get("white_counts", {})
    reds = data.get("red_counts", {})

    if not whites or not reds:
        logger.warning("No valid frequency data found in analysis file.")
        return

    # Convert keys/values to numeric lists
    try:
        white_nums = [int(k) for k in whites.keys()]
        white_vals = [float(v) for v in whites.values()]
        red_nums = [int(k) for k in reds.keys()]
        red_vals = [float(v) for v in reds.values()]
    except ValueError as e:
        logger.error("Failed to convert data types for plotting: %s", e)
        return

    # ── Create subplots ─────────────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # White Ball Chart
    ax1.bar(white_nums, white_vals, color="steelblue", edgecolor="black")
    ax1.set_title("White Ball Frequencies", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Ball Number")
    ax1.set_ylabel("Weighted Count")
    ax1.set_xticks(range(1, 70, 2))  # 1–69 (skip every other label)
    ax1.tick_params(axis="x", labelrotation=90, labelsize=7)
    ax1.grid(alpha=0.3)

    # Red Ball Chart
    ax2.bar(red_nums, red_vals, color="tomato", edgecolor="black")
    ax2.set_title("Red Ball Frequencies", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Ball Number")
    ax2.set_ylabel("Weighted Count")
    ax2.set_xticks(range(1, 27))
    ax2.tick_params(axis="x", labelrotation=90, labelsize=8)
    ax2.grid(alpha=0.3)

    plt.tight_layout()

    # ── Auto-Save Option ───────────────────────────────────────
    if save_plots:
        output_dir = Path("data/plots")
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / f"{json_file.stem}.png"
        try:
            plt.savefig(out_file, dpi=150)
            logger.info("🖼️  Plot saved to %s", out_file)
            print(f"🖼️  Plot saved to {out_file}")
        except Exception as e:
            logger.error("Failed to save plot: %s", e)

    plt.close(fig)


# ──────────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    latest_json = max(
        Path("data").glob("analysis_*.json"),
        key=os.path.getmtime,
        default=None,
    )
    if latest_json:
        plot_analysis(latest_json)
    else:
        print("⚠️ No analysis JSON file found in /data")
