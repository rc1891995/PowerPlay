# ──────────────────────────────────────────────────────────────
# MODULE: dashboard_app.py
# PURPOSE: Simple Powerball dashboard (CSV-only, multi-strategy picks)
# VERSION: PowerPlay v3.1 (clean reset)
# ──────────────────────────────────────────────────────────────

from __future__ import annotations

import os
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import streamlit as st

# Make project root importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data_io import load_draws  # type: ignore
from utils.logger import get_logger  # type: ignore

logger = get_logger(__name__)

DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "powerball_draws.csv"
LOG_PATH = Path("logs/powerplay.log")
PATTERN_CSV = DATA_DIR / "analysis_patterns_extended.csv"
HIST_PNG = DATA_DIR / "pattern_histogram.png"
TOPBOT_PNG = DATA_DIR / "patterns_top_bottom.png"
TREND_PNG = DATA_DIR / "patterns_trend.png"
TREND_SHORT_PNG = DATA_DIR / "patterns_trend_short.png"
TREND_LONG_PNG = DATA_DIR / "patterns_trend_long.png"

try:
    from version import __version__ as PP_VERSION  # type: ignore
except Exception:  # pragma: no cover
    PP_VERSION = "3.1"


# ──────────────────────────────────────────────────────────────
# DATA NORMALIZATION
# ──────────────────────────────────────────────────────────────


@dataclass
class Record:
    date: datetime
    whites: List[int]
    red: int


@dataclass
class PickSet:
    strategy: str
    description: str
    whites: List[int]
    red: int


def _parse_date(s: str) -> datetime | None:
    """Best-effort parse of draw_date from CSV."""
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def normalize_draws(raw_draws: List[Dict[str, Any]]) -> List[Record]:
    records: List[Record] = []
    for d in raw_draws:
        date_str = str(d.get("draw_date", "")).strip()
        dt = _parse_date(date_str)
        if dt is None:
            continue

        whites_raw = d.get("whites") or d.get("white_balls") or []
        try:
            whites = [int(x) for x in whites_raw]
        except Exception:
            continue

        try:
            red = int(d.get("red"))
        except Exception:
            continue

        if len(whites) != 5:
            continue

        records.append(Record(date=dt, whites=whites, red=red))

    records.sort(key=lambda r: r.date)
    return records


# ──────────────────────────────────────────────────────────────
# STRATEGY HELPERS
# ──────────────────────────────────────────────────────────────


def _basic_counts(records: List[Record]) -> tuple[Counter, Counter]:
    whites = Counter()
    reds = Counter()
    for r in records:
        whites.update(r.whites)
        reds[r.red] += 1
    return whites, reds


def _weighted_counts(
    records: List[Record], base: float = 0.995
) -> tuple[Counter, Counter]:
    """Exponential recency weighting: newer draws count more."""
    n = len(records)
    whites = Counter()
    reds = Counter()

    for i, r in enumerate(records):
        w = base ** (n - i - 1)
        for num in r.whites:
            whites[num] += w
        reds[r.red] += w

    return whites, reds


def _next_draw_weekday(from_date: datetime | None = None) -> int:
    """Approximate next draw weekday for Powerball (Mon, Wed, Sat)."""
    draw_days = {0, 2, 5}  # Mon, Wed, Sat
    current = from_date or datetime.now()
    for i in range(1, 8):
        candidate = current + timedelta(days=i)
        if candidate.weekday() in draw_days:
            return candidate.weekday()
    return current.weekday()


def _overdue_order(records: List[Record]) -> tuple[List[int], List[int]]:
    """Return whites and reds ordered by 'days since last seen' (descending)."""
    if not records:
        return [], []

    last_seen_white: dict[int, datetime] = {}
    last_seen_red: dict[int, datetime] = {}

    for rec in records:
        for n in rec.whites:
            last_seen_white[n] = rec.date
        last_seen_red[rec.red] = rec.date

    first_date = records[0].date
    latest_date = records[-1].date

    # Fill missing numbers (treat as very overdue)
    for n in range(1, 70):
        last_seen_white.setdefault(n, first_date)
    for n in range(1, 27):
        last_seen_red.setdefault(n, first_date)

    def ordered(mapping: dict[int, datetime]) -> List[int]:
        return [
            n
            for n, _ in sorted(
                ((num, (latest_date - dt).days) for num, dt in mapping.items()),
                key=lambda x: x[1],
                reverse=True,
            )
        ]

    return ordered(last_seen_white), ordered(last_seen_red)


# ──────────────────────────────────────────────────────────────
# STRATEGIES (GLOBAL_HOT, RECENCY_WEIGHTED, BALANCED, OVERDUE)
# ──────────────────────────────────────────────────────────────


def strategy_global_hot(records: List[Record]) -> PickSet:
    """Pure frequency over all draws."""
    whites, reds = _basic_counts(records)

    white_pool = [n for n, _ in whites.most_common(15)] or list(range(1, 70))
    red_pool = [n for n, _ in reds.most_common(5)] or list(range(1, 27))

    k = min(5, len(white_pool))
    whites_pick = sorted(random.sample(white_pool, k=k))
    red_pick = random.choice(red_pool)

    return PickSet(
        strategy="GLOBAL_HOT",
        description="Top historical frequencies across all draws.",
        whites=whites_pick,
        red=red_pick,
    )


def strategy_recency_weighted(records: List[Record]) -> PickSet:
    """Recent draws weighted more heavily (exponential decay)."""
    if not records:
        return strategy_global_hot(records)

    whites, reds = _weighted_counts(records, base=0.995)

    white_pool = [n for n, _ in whites.most_common(20)] or list(range(1, 70))
    red_pool = [n for n, _ in reds.most_common(8)] or list(range(1, 27))

    k = min(5, len(white_pool))
    whites_pick = sorted(random.sample(white_pool, k=k))
    red_pick = random.choice(red_pool)

    return PickSet(
        strategy="RECENCY_WEIGHTED",
        description="Recent draws count more (exponential decay weighting).",
        whites=whites_pick,
        red=red_pick,
    )


def strategy_balanced(records: List[Record]) -> PickSet:
    """
    Mix of hot / mid / cold:
      - 3 from top 30
      - 1 from middle band
      - 1 from bottom band (cold)
    """
    if not records:
        return strategy_global_hot(records)

    whites, reds = _basic_counts(records)
    sorted_whites = [n for n, _ in whites.most_common()]

    if len(sorted_whites) < 5:
        return strategy_global_hot(records)

    top_band = sorted_whites[:30]
    mid_band = (
        sorted_whites[30:45]
        if len(sorted_whites) > 45
        else sorted_whites[30:-10] or sorted_whites[30:]
    )
    cold_band = sorted_whites[-15:]

    picks: List[int] = []
    if top_band:
        picks.extend(random.sample(top_band, k=min(3, len(top_band))))
    if mid_band:
        picks.extend(random.sample(mid_band, k=1))
    if cold_band:
        picks.extend(random.sample(cold_band, k=1))

    whites_pick = sorted(picks[:5])

    red_sorted = [n for n, _ in reds.most_common()]
    if red_sorted:
        mid_index = max(1, len(red_sorted) // 3)
        pool = red_sorted[: mid_index + 3]
        red_pick = random.choice(pool)
    else:
        red_pick = random.randint(1, 26)

    return PickSet(
        strategy="BALANCED",
        description="3 hot, 1 mid, 1 cold – blended coverage.",
        whites=whites_pick,
        red=red_pick,
    )


def strategy_overdue(records: List[Record]) -> PickSet:
    """Numbers with the longest time since last seen."""
    whites_ordered, reds_ordered = _overdue_order(records)

    if not whites_ordered:
        return strategy_global_hot(records)

    whites_pick = sorted(whites_ordered[:5])
    red_pick = reds_ordered[0] if reds_ordered else random.randint(1, 26)

    return PickSet(
        strategy="OVERDUE",
        description="Numbers with the longest gap since last seen.",
        whites=whites_pick,
        red=red_pick,
    )


# ──────────────────────────────────────────────────────────────
# STREAMLIT PAGE CONFIG
# ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PowerPlay Dashboard – Powerball",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎰 PowerPlay Dashboard – Powerball Only (CSV)")
st.caption("Lightweight v3.1 reset – CSV-based, no DB, no Mega Millions.")


# Sidebar footer / meta
st.sidebar.header("ℹ️ About")
st.sidebar.write("PowerPlay – local Powerball analysis & picks.")
st.sidebar.caption(f"Version: {PP_VERSION}")


# ──────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────

if not CSV_PATH.exists():
    st.error(
        "No Powerball CSV found at `data/powerball_draws.csv`.\n\n"
        "Run `python -m scripts.backfill_powerball_ny` in your terminal first."
    )
    st.stop()

raw_draws = load_draws(CSV_PATH)
records = normalize_draws(raw_draws)

if not records:
    st.error("No valid Powerball draws could be parsed from the CSV.")
    st.stop()

# Last updated timestamp
mod = datetime.fromtimestamp(CSV_PATH.stat().st_mtime)
st.caption(f"🕓 Draw cache last updated: {mod.strftime('%b %d %Y %H:%M')} (local time)")


# ──────────────────────────────────────────────────────────────
# SECTION 1 – MULTI-STRATEGY RECOMMENDED PICKS
# ──────────────────────────────────────────────────────────────

st.header("🎯 Multi-Strategy Powerball Picks")

col_left, col_right = st.columns(2)

with col_left:
    hot_pick = strategy_global_hot(records)
    recency_pick = strategy_recency_weighted(records)

    st.subheader("🔥 GLOBAL_HOT")
    whites_str = " ".join(f"{n:02d}" for n in hot_pick.whites)
    st.write(hot_pick.description)
    st.markdown(
        f"**Whites:** {whites_str} &nbsp;&nbsp; **Powerball:** {hot_pick.red:02d}"
    )
    st.markdown("---")

    st.subheader("⏱️ RECENCY_WEIGHTED")
    whites_str = " ".join(f"{n:02d}" for n in recency_pick.whites)
    st.write(recency_pick.description)
    st.markdown(
        f"**Whites:** {whites_str} &nbsp;&nbsp; **Powerball:** {recency_pick.red:02d}"
    )

with col_right:
    balanced_pick = strategy_balanced(records)
    overdue_pick = strategy_overdue(records)

    st.subheader("⚖️ BALANCED")
    whites_str = " ".join(f"{n:02d}" for n in balanced_pick.whites)
    st.write(balanced_pick.description)
    st.markdown(
        f"**Whites:** {whites_str} &nbsp;&nbsp; **Powerball:** {balanced_pick.red:02d}"
    )
    st.markdown("---")

    st.subheader("⌛ OVERDUE")
    whites_str = " ".join(f"{n:02d}" for n in overdue_pick.whites)
    st.write(overdue_pick.description)
    st.markdown(
        f"**Whites:** {whites_str} &nbsp;&nbsp; **Powerball:** {overdue_pick.red:02d}"
    )


# ──────────────────────────────────────────────────────────────
# SECTION 2 – LATEST 10 DRAWS
# ──────────────────────────────────────────────────────────────

st.header("🧾 Latest 10 Draws")

# Build a DataFrame purely from records so we don't depend on CSV shape quirks
latest_records = sorted(records, key=lambda r: r.date, reverse=True)[:10]
latest_records = list(reversed(latest_records))  # show oldest→newest in table

table_rows = []
for r in latest_records:
    row = {
        "Date": r.date.strftime("%Y-%m-%d"),
        "W1": r.whites[0],
        "W2": r.whites[1],
        "W3": r.whites[2],
        "W4": r.whites[3],
        "W5": r.whites[4],
        "Powerball": r.red,
    }
    table_rows.append(row)

df_latest = pd.DataFrame(table_rows)
st.dataframe(df_latest, hide_index=True, width="stretch")


# ──────────────────────────────────────────────────────────────
# SECTION 3 – PATTERNS & CHI-SQUARE SUMMARY (STATIC FILES)
# ──────────────────────────────────────────────────────────────

st.header("📈 Patterns, Randomness & Trends")

tab_summary, tab_hist, tab_topbot, tab_trend = st.tabs(
    ["Summary", "Histogram", "Top/Bottom 10", "Rolling Trends"]
)

# --- TAB: SUMMARY ---
with tab_summary:
    chi2_val = None
    p_val = None

    if LOG_PATH.exists():
        try:
            with LOG_PATH.open("r", encoding="utf-8") as f:
                lines = f.readlines()

            pattern = re.compile(r"χ²\s*=\s*([\d.]+).*p\s*=\s*([\d.]+)")
            for line in reversed(lines):
                m = pattern.search(line)
                if m:
                    chi2_val = float(m.group(1))
                    p_val = float(m.group(2))
                    break
        except Exception as exc:  # pragma: no cover
            logger.warning("Could not parse chi-square results: %s", exc)

    col1, col2 = st.columns(2)
    col1.metric("Chi-Square (χ²)", f"{chi2_val:.2f}" if chi2_val is not None else "—")
    col2.metric("p-Value", f"{p_val:.4f}" if p_val is not None else "—")

    if p_val is not None:
        if p_val < 0.05:
            st.error("❗ Possible non-uniform pattern detected (p < 0.05).")
        else:
            st.success("✅ Distribution appears statistically uniform (p ≥ 0.05).")
    else:
        st.info(
            "Run `python -m scripts.analyze_patterns_extended` to recompute chi-square statistics."
        )

    if PATTERN_CSV.exists():
        with st.expander("View raw pattern data (top 15)"):
            df_patterns = pd.read_csv(PATTERN_CSV)
            st.dataframe(df_patterns.head(15), hide_index=True, width="stretch")
    else:
        st.info(
            "Pattern CSV not found. Run `python -m scripts.analyze_patterns_extended` to generate it."
        )


# --- TAB: HISTOGRAM ---
with tab_hist:
    if HIST_PNG.exists():
        st.image(
            str(HIST_PNG), caption="White Ball Frequency Distribution", width="stretch"
        )
    else:
        st.info(
            "Histogram image not found. Run `python -m scripts.plot_patterns` to generate it."
        )


# --- TAB: TOP/BOTTOM 10 ---
with tab_topbot:
    if TOPBOT_PNG.exists():
        st.image(
            str(TOPBOT_PNG), caption="Top 10 vs Bottom 10 White Balls", width="stretch"
        )
    else:
        st.info(
            "Top/Bottom chart not found. Run `python -m scripts.plot_patterns` to generate it."
        )


# --- TAB: ROLLING TRENDS ---
with tab_trend:
    if TREND_SHORT_PNG.exists() or TREND_LONG_PNG.exists() or TREND_PNG.exists():
        cols = st.columns(2)
        if TREND_SHORT_PNG.exists():
            cols[0].image(
                str(TREND_SHORT_PNG), caption="Short Window Trends", width="stretch"
            )
        if TREND_LONG_PNG.exists():
            cols[1].image(
                str(TREND_LONG_PNG), caption="Long Window Trends", width="stretch"
            )

        if TREND_PNG.exists():
            st.image(str(TREND_PNG), caption="Combined Trend View", width="stretch")
    else:
        st.info(
            "Trend plots not found. Run `python -m scripts.plot_trends` (and related tools) "
            "to generate rolling trend images."
        )
