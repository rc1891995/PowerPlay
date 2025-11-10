# ──────────────────────────────────────────────────────────────
# MODULE: recommend_powerball.py
# PURPOSE: Generate Powerball number recommendations.
# UPDATED: Sprint 2.3.4 – Adds multi-exact pick mode & refined weight logic.
# ──────────────────────────────────────────────────────────────
"""
Generates Powerball number recommendations using frequency
analysis data. Supports deterministic (“exact”) selections,
probability-weighted random draws, and optional CSV export.

Features:
    • Deterministic exact picks for repeatable results
    • Weighted or uniform random generation
    • CSV logging & dashboard integration
"""

import csv
import os
import random
from collections import Counter

from utils.data_io import count_frequencies, load_draws
from utils.logger import get_logger

logger = get_logger(__name__)

# pylint: disable=redefined-outer-name,too-many-arguments,too-many-locals


# ──────────────────────────────────────────────────────────────
# FUNCTION: pick_numbers
# PURPOSE: Generate Powerball recommendations (weighted or uniform)
# ──────────────────────────────────────────────────────────────
def pick_numbers(
    white_counts: Counter,
    red_counts: Counter,
    mode: str = "hot",
    count: int = 1,
    exact: bool = False,
    use_weights: bool = False,
) -> list[dict]:
    """
    Generate Powerball number recommendations.

    Args:
        white_counts (Counter): Frequency counts for white balls.
        red_counts (Counter): Frequency counts for red balls.
        mode (str): "hot" for most frequent, "cold" for least.
        count (int): Number of picks to generate.
        exact (bool): Return deterministic top/bottom picks.
        use_weights (bool): Use weighted randomness if True.

    Returns:
        list[dict]: List of recommended pick dictionaries.
    """
    if mode == "hot":
        sorted_whites = white_counts.most_common()
        sorted_reds = red_counts.most_common()
    elif mode == "cold":
        sorted_whites = list(reversed(white_counts.most_common()))
        sorted_reds = list(reversed(red_counts.most_common()))
    else:
        raise ValueError("Invalid mode: must be 'hot' or 'cold'")

    # ──────────────────────────────────────────────
    # DETERMINISTIC EXACT MODE
    # ──────────────────────────────────────────────
    if exact:
        picks = []
        for i in range(count):
            whites = sorted([n for n, _ in sorted_whites[i : i + 5]])
            if len(whites) < 5:
                break
            red = sorted_reds[i % len(sorted_reds)][0]
            picks.append({"whites": whites, "red": red})

        logger.info(
            "🎯 Generated %d deterministic pick(s) in '%s' mode",
            len(picks),
            mode,
        )
        return picks

    # ──────────────────────────────────────────────
    # RANDOMIZED MODE
    # ──────────────────────────────────────────────
    top_whites = sorted_whites[:20]
    top_reds = sorted_reds[:10]
    recommendations = []

    for _ in range(count):
        if use_weights:
            # Weighted white ball selection
            w_nums = [n for n, _ in top_whites]
            w_weights = [freq for _, freq in top_whites]
            whites = sorted(random.choices(w_nums, weights=w_weights, k=20))
            whites = sorted(list(dict.fromkeys(whites))[:5])  # dedupe + truncate

            if len(whites) < 5:
                extras = [n for n in w_nums if n not in whites]
                whites += random.sample(extras, 5 - len(whites))

            # Weighted red ball selection
            r_nums = [n for n, _ in top_reds]
            r_weights = [freq for _, freq in top_reds]
            red = random.choices(r_nums, weights=r_weights, k=1)[0]
        else:
            # Uniform random draws
            whites = sorted(random.sample([n for n, _ in top_whites], 5))
            red = random.choice([n for n, _ in top_reds])

        recommendations.append({"whites": whites, "red": red})

    logger.info(
        "🎯 Generated %d %srandomized pick(s) in '%s' mode",
        count,
        "weighted " if use_weights else "",
        mode,
    )
    return recommendations


# ──────────────────────────────────────────────────────────────
# FUNCTION: colorize
# PURPOSE: Optional CLI color formatting
# ──────────────────────────────────────────────────────────────
def colorize(num, hot_threshold, cold_threshold):
    """Return ANSI-colored string based on frequency thresholds."""
    if num >= hot_threshold:
        return f"\033[91m{num:02d}\033[0m"  # 🔥 hot/red
    if num <= cold_threshold:
        return f"\033[94m{num:02d}\033[0m"  # 🧊 cold/blue
    return f"\033[92m{num:02d}\033[0m"  # 💚 neutral


# ──────────────────────────────────────────────────────────────
# FUNCTION: run
# PURPOSE: Execute the recommendation workflow
# ──────────────────────────────────────────────────────────────
def run(args):  # pylint: disable=too-many-locals
    """
    Main CLI or dashboard entrypoint for generating recommendations.

    Args:
        args (Namespace-like): Expected attributes:
            - mode (str): "hot" or "cold"
            - count (int): Number of picks
            - exact (bool): Deterministic mode
            - use_weights (bool): Weighted randomness
            - save_picks (bool): Save to CSV (optional)
    """
    logger.info(
        "🎯 [Recommend] Started | mode=%s | count=%d | exact=%s | weighted=%s",
        args.mode,
        args.count,
        args.exact,
        args.use_weights,
    )

    draws = load_draws()
    white_counts, red_counts = count_frequencies(draws)

    print(f"\n🎯 [Recommend] Mode: {args.mode} | Generating {args.count} picks\n")

    recs = pick_numbers(
        white_counts,
        red_counts,
        mode=args.mode,
        count=args.count,
        exact=args.exact,
        use_weights=args.use_weights,
    )

    # ── Display Picks ──
    for i, r in enumerate(recs, start=1):
        whites_str = " ".join(f"{n:02d}" for n in r["whites"])
        print(f"Pick {i}: {whites_str}  🔴 {r['red']:02d}")

    print(
        "\n✨ Tip: use '--exact' for deterministic top/bottom picks "
        "or '--use-weights' for probability-biased random draws.\n"
    )

    # ── Weighted Bias Summary ──
    if args.use_weights:
        total_w = sum(freq for _, freq in white_counts.most_common(20))
        top_ball, top_freq = white_counts.most_common(1)[0]
        bias_pct = (top_freq / total_w) * 100
        logger.info(
            "📈 Weighted bias: hottest ball %d contributes %.1f%% of total weight",
            top_ball,
            bias_pct,
        )

    # ── Optional CSV Export ──
    if getattr(args, "save_picks", False):
        os.makedirs("data", exist_ok=True)
        out_path = os.path.join("data", "recommended_picks.csv")
        with open(out_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for r in recs:
                writer.writerow(r["whites"] + [r["red"]])
        print(f"💾 Saved picks to {out_path}")
        logger.info("💾 Saved %d recommended picks to %s", len(recs), out_path)

    logger.info("✅ Recommendation workflow complete.")


# ──────────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from types import SimpleNamespace

    args = SimpleNamespace(
        mode="hot",
        count=3,
        exact=False,
        use_weights=True,
        save_picks=False,
    )
    run(args)
