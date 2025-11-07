"""
Analyze Visuals Module
----------------------
Generates bar charts for PowerPlay white/red ball frequencies.
Auto-saves PNGs and displays interactive charts.
"""

# ──────────────────────────────────────────────────────────────
# Standard Library Imports
# ──────────────────────────────────────────────────────────────
import os
import json

# ──────────────────────────────────────────────────────────────
# Third-Party Imports
# ──────────────────────────────────────────────────────────────
import matplotlib

matplotlib.use("TkAgg")  # must set backend before pyplot import
import matplotlib.pyplot as plt


# ──────────────────────────────────────────────────────────────
# FUNCTION: plot_analysis
# PURPOSE: Display and save frequency charts for whites and reds
# ──────────────────────────────────────────────────────────────
def plot_analysis(json_path, save_plots=True):
    """Generate bar charts for white/red ball frequencies and optionally save PNGs."""

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    whites = data["white_counts"]
    reds = data["red_counts"]

    white_nums = [int(k) for k in whites.keys()]
    white_vals = list(whites.values())
    red_nums = [int(k) for k in reds.keys()]
    red_vals = list(reds.values())

    _, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # ── White Ball Chart ───────────────────────────────────────
    ax1.bar(white_nums, white_vals, color="steelblue")
    ax1.set_title("White Ball Frequencies")
    ax1.set_xlabel("Ball Number")
    ax1.set_ylabel("Weighted Count")
    ax1.set_xticks(range(1, 70))  # Powerball whites go 1–69
    ax1.tick_params(axis="x", labelrotation=90, labelsize=8)

    # ── Red Ball Chart ─────────────────────────────────────────
    ax2.bar(red_nums, red_vals, color="tomato")
    ax2.set_title("Red Ball Frequencies")
    ax2.set_xlabel("Ball Number")
    ax2.set_ylabel("Weighted Count")
    ax2.set_xticks(range(1, 27))  # Powerball reds go 1–26
    ax2.tick_params(axis="x", labelrotation=90, labelsize=8)

    plt.tight_layout()

    # ── Auto-Save Option ───────────────────────────────────────
    if save_plots:
        os.makedirs("data/plots", exist_ok=True)
        base_name = os.path.splitext(os.path.basename(json_path))[0]
        out_file = os.path.join("data/plots", f"{base_name}.png")
        plt.savefig(out_file, dpi=150)
        print(f"🖼️  Plot saved to {out_file}")

    plt.show()
