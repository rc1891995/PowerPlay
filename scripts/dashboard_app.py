# ──────────────────────────────────────────────────────────────
# MODULE: dashboard_app.py
# PURPOSE: Streamlit dashboard for PowerPlay — visualize, analyze, and recommend Powerball numbers.
# UPDATED: Sprint 2.3.3 – Adds timestamp, Power Play toggle, and multi-trend comparison.
# ──────────────────────────────────────────────────────────────
"""
Streamlit dashboard for PowerPlay — orchestrates fetching, analyzing,
visualizing, and recommending Powerball numbers in an interactive UI.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st

# ────────────────────────────────────────────────
# IMPORT PROJECT MODULES
# ────────────────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.logger import get_logger
from utils.data_io import load_draws
from scripts import (
    analyze_visuals,
    analyze_powerball,
    fetch_powerball,
    recommend_powerball,
    plot_trends,
)

logger = get_logger(__name__)
DATA_PATH = Path("data/powerball_draws.csv")
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ────────────────────────────────────────────────
# PAGE CONFIGURATION
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="PowerPlay Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("🎰 PowerPlay Dashboard – Live Powerball Data")

# --- Display last-updated timestamp ---
if DATA_PATH.exists():
    last_modified = datetime.fromtimestamp(DATA_PATH.stat().st_mtime)
    st.caption(f"🕓 Last updated: {last_modified.strftime('%b %d %Y %H:%M UTC')}")
else:
    st.caption("🕓 No draw data found. Fetch to begin.")

# ────────────────────────────────────────────────
# SECTION 1 – Display Latest Draws
# ────────────────────────────────────────────────
draws_data = load_draws()

# Normalize to DataFrame for consistent rendering
if isinstance(draws_data, list) and draws_data:
    df = pd.DataFrame(draws_data)
elif isinstance(draws_data, pd.DataFrame) and not draws_data.empty:
    df = draws_data
else:
    df = pd.DataFrame(columns=["draw_date", "white_balls", "powerball"])

if not df.empty:
    st.subheader("🧾 Latest 10 Draws")

    # Map possible column names for backward compatibility
    column_map = {
        "draw_date": "Date",
        "date": "Date",
        "white_balls": "White Balls",
        "whites": "White Balls",
        "powerball": "Powerball",
        "red": "Powerball",
    }

    available_cols = [c for c in column_map if c in df.columns]
    df_display = (
        df[available_cols]
        .rename(columns={k: v for k, v in column_map.items() if k in df.columns})
        .sort_values(by="Date", ascending=False)
        .head(10)
    )

    st.dataframe(df_display, use_container_width=True, hide_index=True)
else:
    st.warning("No draw data found. Fetch first.")

# ────────────────────────────────────────────────
# SIDEBAR CONTROLS
# ────────────────────────────────────────────────
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
include_pp = st.sidebar.checkbox("Include Power Play in Analysis", value=False)

# Optional Cloud Sync Controls
st.sidebar.subheader("☁️ Cloud Sync")
upload_to_s3 = st.sidebar.checkbox("Upload latest analysis to S3", value=False)
s3_bucket = st.sidebar.text_input("S3 Bucket Name", value="my-powerplay-data")

# ────────────────────────────────────────────────
# ACTION 1 – Fetch Latest Draws
# ────────────────────────────────────────────────
if fetch_btn:
    FetchArgs = type("Args", (), {"source": "local"})
    fetch_powerball.run(FetchArgs)
    st.success("✅ Fetched/appended latest draws to data/powerball_draws.csv")

# ────────────────────────────────────────────────
# ACTION 2 – Analyze & Visualize
# ────────────────────────────────────────────────
if analyze_btn:
    st.subheader("📊 Frequency Analysis")

    AnalyzeArgs = type(
        "Args",
        (),
        {"last": last_n, "weight_window": weight_window, "include_pp": include_pp},
    )
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
        png_path = Path("data/plots") / png_name

        if png_path.exists():
            st.image(
                str(png_path),
                caption=f"Latest analysis → {png_name}",
                use_container_width=True,
            )
        st.success("📊 Analysis complete and visualized.")
    else:
        st.warning("⚠️ No analysis file found — run analysis first.")

    # Optional S3 Upload
    if upload_to_s3:
        from utils import s3_io

        if latest_json:
            base_name = os.path.splitext(os.path.basename(latest_json))[0]
            png_path = Path("data/plots") / f"{base_name}.png"

            if Path(latest_json).exists():
                s3_io.upload_file(latest_json, s3_bucket, f"analysis/{base_name}.json")
            if png_path.exists():
                s3_io.upload_file(png_path, s3_bucket, f"plots/{base_name}.png")

            st.success(f"☁️ Uploaded analysis and plot to s3://{s3_bucket}/")
        else:
            st.warning("⚠️ No analysis files found to upload.")

# ────────────────────────────────────────────────
# ACTION 3 – Generate Recommendations
# ────────────────────────────────────────────────
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
        import csv

        out_path = Path("data/recommended_picks.csv")
        with open(out_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for r in recs:
                writer.writerow(r["whites"] + [r["red"]])
        st.success(f"💾 Saved picks to {out_path}")

# ────────────────────────────────────────────────
# SECTION 4 – Patterns, Randomness & Trends
# ────────────────────────────────────────────────
st.header("📈 Patterns, Randomness & Trends")

pattern_csv = Path("data/analysis_patterns_extended.csv")
pattern_png = Path("data/pattern_histogram.png")
top_bottom_path = Path("data/patterns_top_bottom.png")

tab_summary, tab_hist, tab_topbot, tab_trends = st.tabs(
    ["Summary", "Histogram", "Top/Bottom 10", "Rolling Trends"]
)

# --- TAB 1: Summary ---
import re

with tab_summary:
    if pattern_csv.exists():
        df_patterns = pd.read_csv(pattern_csv)

        chi2_val, p_val = None, None
        pattern = re.compile(r"χ²\s*=\s*([\d.]+).*p\s*=\s*([\d.]+)")
        try:
            with open("logs/powerplay.log", "r", encoding="utf-8") as f:
                for line in reversed(f.readlines()):
                    match = pattern.search(line)
                    if match:
                        chi2_val = float(match.group(1))
                        p_val = float(match.group(2))
                        break
        except Exception as e:
            logger.warning("Could not parse chi-square results: %s", e)

        col1, col2 = st.columns(2)
        col1.metric("Chi-Square (χ²)", f"{chi2_val:.2f}" if chi2_val else "—")
        col2.metric("p-Value", f"{p_val:.4f}" if p_val else "—")

        if p_val is not None:
            if p_val < 0.05:
                st.error("❗ Possible non-uniform pattern detected (p < 0.05).")
            else:
                st.success("✅ Distribution appears statistically uniform (p ≥ 0.05).")
        else:
            st.warning("⚠️ Could not extract test results from log file.")

        with st.expander("View raw pattern data (top 15)"):
            st.dataframe(df_patterns.head(15))
    else:
        st.info(
            "No pattern analysis found yet. Run `python -m scripts.analyze_patterns_extended` first."
        )

# --- TAB 2: Histogram ---
with tab_hist:
    if pattern_png.exists():
        st.image(
            str(pattern_png),
            caption="White Ball Frequency Distribution (Uniform Expectation in Red)",
            use_container_width=True,
        )
    else:
        st.info(
            "Run `python -m scripts.analyze_patterns_extended` to generate histogram."
        )

# --- TAB 3: Top/Bottom 10 ---
with tab_topbot:
    if top_bottom_path.exists():
        st.image(
            str(top_bottom_path),
            caption="Top 10 Hottest vs Bottom 10 Coldest White Balls",
            use_container_width=True,
        )
    else:
        st.info("Run `python -m scripts.plot_patterns` to generate this chart.")

# --- TAB 4: Rolling Trends (time-series frequency) ---
with tab_trends:
    st.subheader("📈 Rolling Trends – Compare Short vs Long Windows")

    top_n = st.slider("Top N Balls", 3, 10, 5, key="trend_topn")
    short_win = st.slider("Short Window (Draws)", 3, 15, 5, key="trend_short")
    long_win = st.slider("Long Window (Draws)", 15, 60, 20, key="trend_long")

    if st.button("Generate Comparison Plot", key="trend_btn"):
        plot_trends.run(top_n=top_n, window=short_win, suffix="_short")
        plot_trends.run(top_n=top_n, window=long_win, suffix="_long")
        st.success("✅ Generated trend comparison plots")

    short_img = Path("data/patterns_trend_short.png")
    long_img = Path("data/patterns_trend_long.png")

    cols = st.columns(2)
    if short_img.exists():
        cols[0].image(
            str(short_img), caption=f"{short_win}-Draw Window", use_container_width=True
        )
    if long_img.exists():
        cols[1].image(
            str(long_img), caption=f"{long_win}-Draw Window", use_container_width=True
        )
