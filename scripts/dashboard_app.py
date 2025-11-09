"""
Streamlit dashboard for PowerPlay — orchestrates fetching, analyzing,
visualizing, and recommending Powerball numbers in an interactive UI.
"""

import os
import sys
from pathlib import Path

# --- Ensure project root is importable (must come first!) ---
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import pandas as pd
import streamlit as st  # pylint: disable=wrong-import-position
from utils.logger import get_logger
from utils.data_io import load_draws
from scripts import (
    analyze_visuals,
    analyze_powerball,
    fetch_powerball,
    recommend_powerball,
)

logger = get_logger(__name__)
DATA_PATH = Path("data/powerball_draws.csv")

# --- Ensure project root is importable (fixes Streamlit import issue) ---
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # pylint: disable=wrong-import-position

import streamlit as st  # pylint: disable=wrong-import-position
from scripts import (
    analyze_visuals,
    analyze_powerball,
    fetch_powerball,
    recommend_powerball,
)  # pylint: disable=import-error,wrong-import-position
from utils.data_io import (
    load_draws,
)  # pylint: disable=import-error,wrong-import-position


def load_draw_data() -> pd.DataFrame:
    """Load cached Powerball draw data from CSV."""
    if not DATA_PATH.exists():
        logger.error("Data file not found: %s", DATA_PATH)
        st.error("No cached data found. Run `python -m scripts.fetch_powerball --real` first.")
        return pd.DataFrame(columns=["draw_date", "white_balls", "powerball", "power_play"])

    df = pd.read_csv(DATA_PATH)
    logger.info("Loaded %d draws from cache", len(df))
    return df

# --- Streamlit Page Setup ---
st.set_page_config(
    page_title="PowerPlay Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("🎰 PowerPlay Dashboard – Live Powerball Data")
st.caption(f"Data source: {DATA_PATH.resolve()}")

# --- Display latest 10 draws immediately ---
draws_df = load_draw_data()
df = pd.read_csv(DATA_PATH).sort_values(by="draw_date", ascending=False)

if not draws_df.empty:
    st.subheader("🧾 Latest 10 Draws")

    # --- Normalize column naming ---
    cols = ["draw_date", "white_balls", "powerball"]
    df_display = draws_df[cols].head(10)

    # --- Rename headers for readability ---
    df_display = df_display.rename(
        columns={
            "draw_date": "Date",
            "white_balls": "White Balls",
            "powerball": "Powerball",
        }
    )

    # --- Display the streamlined table ---
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning("No draw data found. Fetch first.")

# --- Sidebar Controls ---
st.sidebar.header("Controls")
fetch_btn = st.sidebar.button("📁 Fetch latest draws")
analyze_btn = st.sidebar.button("📊 Analyze & visualize")
recommend_btn = st.sidebar.button("🎯 Generate picks")

last_n = st.sidebar.slider("Analyze last N draws", 5, 100, 20)
weight_window = st.sidebar.slider("Weight window", 0, 50, 10)
mode = st.sidebar.selectbox("Recommendation mode", ["hot", "cold"])
count = st.sidebar.slider("How many picks?", 1, 10, 3)
use_weights = st.sidebar.checkbox("Use weighted randomness", value=True)
exact = st.sidebar.checkbox("Exact pick (ignore randomness)", value=False)
save_picks = st.sidebar.checkbox("Save picks to CSV", value=False)

# S3 integration controls
st.sidebar.subheader("☁️ Cloud Sync")
upload_to_s3 = st.sidebar.checkbox("Upload latest analysis to S3", value=False)
s3_bucket = st.sidebar.text_input("S3 Bucket Name", value="my-powerplay-data")

# --- Data Directory Setup ---
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# --- Action: Fetch Latest Draws ---
if fetch_btn:
    FetchArgs = type("Args", (), {"source": "local"})  # PascalCase to satisfy pylint
    fetch_powerball.run(FetchArgs)
    st.success("✅ Fetched/appended latest draws to data/powerball_draws.csv")

# --- Action: Analyze + Visualize ---
if analyze_btn:
    st.subheader("📊 Frequency Analysis")

    AnalyzeArgs = type(
        "Args", (), {"last": last_n, "weight_window": weight_window}
    )  # PascalCase
    analyze_powerball.run(AnalyzeArgs)

    latest_json = next(
        (
            os.path.join(DATA_DIR, f)
            for f in sorted(os.listdir(DATA_DIR), reverse=True)
            if f.startswith("analysis_") and f.endswith(".json")
        ),
        None,
    )

    if latest_json:
        analyze_visuals.plot_analysis(latest_json, save_plots=True)
        png_name = os.path.splitext(os.path.basename(latest_json))[0] + ".png"
        png_path = os.path.join("data", "plots", png_name)

        if os.path.exists(png_path):
            st.image(
                png_path,
                caption=f"Latest analysis → {os.path.basename(latest_json)}",
                use_container_width=True,
            )
        st.success("📊 Analysis complete and visualized.")
    else:
        st.warning("⚠️ No analysis file found — run analysis first.")

    # ──────────────────────────────────────────────────────────────
    # OPTIONAL: Upload results to S3
    # ──────────────────────────────────────────────────────────────
    if upload_to_s3:
        from utils import s3_io

        if latest_json:
            base_name = os.path.splitext(os.path.basename(latest_json))[0]
            png_path = os.path.join("data", "plots", f"{base_name}.png")

            if os.path.exists(latest_json):
                s3_io.upload_file(latest_json, s3_bucket, f"analysis/{base_name}.json")
            if os.path.exists(png_path):
                s3_io.upload_file(png_path, s3_bucket, f"plots/{base_name}.png")

            st.success(f"☁️ Uploaded analysis and plot to s3://{s3_bucket}/")
        else:
            st.warning("⚠️ No analysis files found to upload.")

# --- Action: Generate Recommendations ---
if recommend_btn:
    st.subheader("🎯 Recommended Picks")

    draws = load_draws()
    white_counts, red_counts = analyze_powerball.analyze(
        draws, last_n=last_n, weight_window=weight_window
    )

    recs = recommend_powerball.pick_numbers(
        white_counts,
        red_counts,
        mode=mode,
        count=count,
        exact=exact,
        use_weights=use_weights,
    )

    for i, r in enumerate(recs, start=1):
        whites_str = " ".join(f"{n:02d}" for n in r["whites"])
        st.write(f"**Pick {i}:** {whites_str}  🔴 {r['red']:02d}")

    if save_picks:
        import csv  # local import to avoid dashboard load cost

        out_path = os.path.join("data", "recommended_picks.csv")
        with open(out_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for r in recs:
                writer.writerow(r["whites"] + [r["red"]])
        st.success(f"💾 Saved picks to {out_path}")

# ──────────────────────────────────────────────────────────────
# SECTION: Recent Activity Log Viewer
# ──────────────────────────────────────────────────────────────
with st.expander("🧾 Recent Activity Log (click to expand)"):
    log_path = os.path.join("logs", "powerplay.log")

    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-20:]  # show last 20 lines
        log_text = "".join(lines)
        st.text_area(
            "Recent Logs",
            value=log_text,
            height=300,
            label_visibility="collapsed",
        )
    else:
        st.info("No log file found yet — run an analysis or recommendation first.")
