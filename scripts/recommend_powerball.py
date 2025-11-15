# ──────────────────────────────────────────────────────────────
# MODULE: recommend_powerball.py
# PURPOSE: Generate multi-strategy Powerball number recommendations
#          based on real historical data in SQLite.
# UPDATED: Sprint 2.5 – DB-backed, multi-model recommendations.
# ──────────────────────────────────────────────────────────────
"""
Generate Powerball number recommendations using real historical data.

Strategies:
  1. GLOBAL_HOT:   Pure frequency over all draws
  2. RECENCY_WEIGHTED: Recent draws count more
  3. DAY_OF_WEEK:  Only draws matching the next draw's weekday
  4. BALANCED:     Mix of hot / mid / cold
  5. OVERDUE:      Numbers with the longest gaps since last seen

Output is printed to the console in a human-friendly format.
"""

from __future__ import annotations

import argparse
import random
import sqlite3
from ast import literal_eval
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = Path("data/powerplay.db")

WHITE_MIN, WHITE_MAX = 1, 69
RED_MIN, RED_MAX = 1, 26


# ──────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ──────────────────────────────────────────────────────────────
@dataclass
class DrawRecord:
    draw_date: datetime
    whites: List[int]
    red: int
    weekday: int  # Monday=0, Sunday=6


@dataclass
class PickSet:
    strategy: str
    description: str
    whites: List[int]
    red: int


# ──────────────────────────────────────────────────────────────
# DB LOADING
# ──────────────────────────────────────────────────────────────
def load_draws_from_db() -> List[DrawRecord]:
    """Load historical draws from SQLite and normalize into DrawRecord list."""
    if not DB_PATH.exists():
        msg = f"Database not found at {DB_PATH}. Run a backfill first."
        logger.error(msg)
        raise FileNotFoundError(msg)

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT draw_date, white_balls, powerball FROM draws ORDER BY draw_date ASC",
            conn,
        )
    finally:
        conn.close()

    if df.empty:
        msg = "No rows found in draws table. Has the backfill completed?"
        logger.error(msg)
        raise ValueError(msg)

    df["draw_date"] = pd.to_datetime(df["draw_date"])

    def parse_whites(val: str | list[int]) -> list[int]:
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            try:
                parsed = literal_eval(val)
                if isinstance(parsed, list):
                    return [int(x) for x in parsed]
            except (SyntaxError, ValueError, TypeError):
                pass
            # Fallback: parse space / comma separated
            parts = str(val).replace("[", "").replace("]", "").split(",")
            return [int(p.strip()) for p in parts if p.strip().isdigit()]
        return []

    df["whites"] = df["white_balls"].apply(parse_whites)
    df["weekday"] = df["draw_date"].dt.weekday

    records: List[DrawRecord] = []
    for row in df.itertuples(index=False):
        if not row.whites or not isinstance(row.powerball, (int, float)):
            continue
        records.append(
            DrawRecord(
                draw_date=row.draw_date,
                whites=[int(w) for w in row.whites],
                red=int(row.powerball),
                weekday=int(row.weekday),
            )
        )

    logger.info("Loaded %d normalized draws from DB", len(records))
    return records


# ──────────────────────────────────────────────────────────────
# COMMON HELPERS
# ──────────────────────────────────────────────────────────────
def next_draw_weekday(from_date: datetime | None = None) -> int:
    """
    Estimate the next Powerball draw weekday (Mon/Wed/Sat).
    Uses local clock if from_date is not provided.
    """
    draw_days = {0, 2, 5}  # Mon, Wed, Sat
    current = from_date or datetime.now()
    one_day = timedelta(days=1)
    while True:
        current += one_day
        if current.weekday() in draw_days:
            return current.weekday()


def weighted_count_whites(
    records: Iterable[DrawRecord], weights: Iterable[float] | None = None
) -> Counter:
    """Count white ball frequencies, optionally applying per-draw weights."""
    counter: Counter = Counter()
    if weights is None:
        for rec in records:
            counter.update(rec.whites)
        return counter

    for rec, w in zip(records, weights):
        for n in rec.whites:
            counter[n] += w
    return counter


def weighted_count_reds(
    records: Iterable[DrawRecord], weights: Iterable[float] | None = None
) -> Counter:
    """Count red (Powerball) frequencies, optionally with weights."""
    counter: Counter = Counter()
    if weights is None:
        for rec in records:
            counter[rec.red] += 1
        return counter

    for rec, w in zip(records, weights):
        counter[rec.red] += w
    return counter


def pick_from_counter(counter: Counter, k: int, descending: bool = True) -> List[int]:
    """Pick k unique numbers from a Counter, ordered by frequency."""
    items = sorted(counter.items(), key=lambda x: x[1], reverse=descending)
    nums = [n for (n, _) in items]
    if len(nums) < k:
        return nums
    return nums[:k]


def sample_from_range(
    start: int, end: int, exclude: Iterable[int] | None = None, k: int = 1
) -> List[int]:
    """Sample k distinct numbers from [start, end], excluding a set."""
    exclude_set = set(exclude or [])
    pool = [n for n in range(start, end + 1) if n not in exclude_set]
    if len(pool) < k:
        return pool
    return random.sample(pool, k)


# ──────────────────────────────────────────────────────────────
# STRATEGIES
# ──────────────────────────────────────────────────────────────
def strategy_global_hot(records: List[DrawRecord]) -> PickSet:
    """Pure frequency over full history."""
    white_freq = weighted_count_whites(records, None)
    red_freq = weighted_count_reds(records, None)

    whites = pick_from_counter(white_freq, 15)  # top 15 pool
    whites_pick = sorted(random.sample(whites, 5))
    reds = pick_from_counter(red_freq, 5)
    red_pick = random.choice(reds) if reds else random.randint(RED_MIN, RED_MAX)

    return PickSet(
        strategy="GLOBAL_HOT",
        description="Top historical frequencies across all draws.",
        whites=whites_pick,
        red=red_pick,
    )


def strategy_recency_weighted(records: List[DrawRecord]) -> PickSet:
    """Recent draws weighted more heavily (exponential decay)."""
    n = len(records)
    # Newest draw gets weight ~1.0, oldest gets much smaller
    base = 0.995
    weights = [base ** (n - i - 1) for i in range(n)]

    white_freq = weighted_count_whites(records, weights)
    red_freq = weighted_count_reds(records, weights)

    whites_pool = pick_from_counter(white_freq, 20)
    whites_pick = sorted(random.sample(whites_pool, 5))
    red_pool = pick_from_counter(red_freq, 8)
    red_pick = random.choice(red_pool) if red_pool else random.randint(RED_MIN, RED_MAX)

    return PickSet(
        strategy="RECENCY_WEIGHTED",
        description="Recent draws count more (exponential decay weighting).",
        whites=whites_pick,
        red=red_pick,
    )


def strategy_day_of_week(records: List[DrawRecord]) -> PickSet:
    """Use only draws whose weekday matches the next draw's weekday."""
    target_weekday = next_draw_weekday()
    filtered = [r for r in records if r.weekday == target_weekday]

    if not filtered:
        # Fallback to global
        logger.warning(
            "No records found for weekday %s – falling back to GLOBAL_HOT",
            target_weekday,
        )
        return strategy_global_hot(records)

    white_freq = weighted_count_whites(filtered, None)
    red_freq = weighted_count_reds(filtered, None)

    whites_pool = pick_from_counter(white_freq, 15)
    whites_pick = sorted(random.sample(whites_pool, 5))
    red_pool = pick_from_counter(red_freq, 5)
    red_pick = random.choice(red_pool) if red_pool else random.randint(RED_MIN, RED_MAX)

    return PickSet(
        strategy="DAY_OF_WEEK",
        description="Only draws that match the upcoming draw's weekday.",
        whites=whites_pick,
        red=red_pick,
    )


def strategy_balanced(records: List[DrawRecord]) -> PickSet:
    """
    Mix of hot / mid / cold:
      - 3 from top 30
      - 1 from middle band
      - 1 from bottom band (cold)
    """
    white_freq = weighted_count_whites(records, None)
    red_freq = weighted_count_reds(records, None)

    sorted_whites = sorted(
        white_freq.items(), key=lambda x: x[1], reverse=True
    )  # (number, freq)
    nums = [n for (n, _) in sorted_whites]

    if len(nums) < 5:
        return strategy_global_hot(records)

    top_band = nums[:30]
    mid_band = nums[30:45] if len(nums) > 45 else nums[30:-10] or nums[30:]
    cold_band = nums[-15:]

    picks: List[int] = []
    picks.extend(random.sample(top_band, k=min(3, len(top_band))))
    if mid_band:
        picks.extend(random.sample(mid_band, k=1))
    if cold_band:
        picks.extend(random.sample(cold_band, k=1))

    whites_pick = sorted(picks[:5])

    # For red, bias slightly toward mid-range popular ones
    red_sorted = [
        n for (n, _) in sorted(red_freq.items(), key=lambda x: x[1], reverse=True)
    ]
    if red_sorted:
        mid_index = max(1, len(red_sorted) // 3)
        pool = red_sorted[: mid_index + 3]
        red_pick = random.choice(pool)
    else:
        red_pick = random.randint(RED_MIN, RED_MAX)

    return PickSet(
        strategy="BALANCED",
        description="3 hot, 1 mid, 1 cold – blended coverage.",
        whites=whites_pick,
        red=red_pick,
    )


def strategy_overdue(records: List[DrawRecord]) -> PickSet:
    """Numbers with the longest time since last seen."""
    last_seen_white: dict[int, datetime] = {}
    last_seen_red: dict[int, datetime] = {}

    for rec in records:
        for n in rec.whites:
            last_seen_white[n] = rec.draw_date
        last_seen_red[rec.red] = rec.draw_date

    # Fill in numbers that have never appeared (treat as very overdue)
    min_date = records[0].draw_date if records else datetime(2000, 1, 1)
    for n in range(WHITE_MIN, WHITE_MAX + 1):
        last_seen_white.setdefault(n, min_date)
    for n in range(RED_MIN, RED_MAX + 1):
        last_seen_red.setdefault(n, min_date)

    now = records[-1].draw_date if records else datetime.now()

    def overdue_sorted(mapping: dict[int, datetime]) -> List[Tuple[int, float]]:
        return sorted(
            ((n, (now - dt).days) for n, dt in mapping.items()),
            key=lambda x: x[1],
            reverse=True,
        )

    whites_overdue = [n for (n, _) in overdue_sorted(last_seen_white)]
    reds_overdue = [n for (n, _) in overdue_sorted(last_seen_red)]

    whites_pick = sorted(whites_overdue[:5])
    red_pick = reds_overdue[0] if reds_overdue else random.randint(RED_MIN, RED_MAX)

    return PickSet(
        strategy="OVERDUE",
        description="Numbers with the longest gap since last seen.",
        whites=whites_pick,
        red=red_pick,
    )


# ──────────────────────────────────────────────────────────────
# CLI ENTRYPOINT
# ──────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate PowerPlay Powerball recommendations from SQLite history."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducible picks.",
    )
    return parser.parse_args()


def format_pickset(pick: PickSet) -> str:
    whites_str = " ".join(f"{n:02d}" for n in sorted(pick.whites))
    return (
        f"[{pick.strategy}] {pick.description}\n"
        f"  Whites: {whites_str}  |  Powerball: {pick.red:02d}\n"
    )


def main() -> None:
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    records = load_draws_from_db()

    strategies = [
        strategy_global_hot,
        strategy_recency_weighted,
        strategy_day_of_week,
        strategy_balanced,
        strategy_overdue,
    ]

    print("\n🎯 PowerPlay – Multi-Strategy Recommendations\n")
    print(f"Loaded {len(records)} historical draws from {DB_PATH}")
    print("All picks are for entertainment only – no guarantees. 😉\n")

    for strat in strategies:
        try:
            pick = strat(records)
            print(format_pickset(pick))
        except Exception as exc:  # pragma: no cover – defensive
            logger.error("Strategy %s failed: %s", strat.__name__, exc)


if __name__ == "__main__":
    main()
