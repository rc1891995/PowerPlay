"""
plot_patterns.py – Generates rolling frequency charts for PowerPlay.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_PATH = Path("data/analysis_patterns_extended.csv")
OUT_PATH = Path("data/patterns_top_bottom.png")

def run(top_n: int = 10):
    if not DATA_PATH.exists():
        print("❌ No analysis_patterns_extended.csv found.")
        return

    df = pd.read_csv(DATA_PATH)

    # Sort by count
    top = df.nlargest(top_n, "count")
    bottom = df.nsmallest(top_n, "count")

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    top.plot.bar(x="white_ball", y="count", ax=axes[0], title=f"Top {top_n} Hottest Balls")
    bottom.plot.bar(x="white_ball", y="count", ax=axes[1], title=f"Bottom {top_n} Coldest Balls")

    fig.tight_layout()
    OUT_PATH.parent.mkdir(exist_ok=True, parents=True)
    plt.savefig(OUT_PATH)
    plt.close(fig)

    print(f"✅ Saved → {OUT_PATH}")

if __name__ == "__main__":
    run()
