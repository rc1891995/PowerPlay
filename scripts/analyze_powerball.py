# ──────────────────────────────────────────────────────────────
# MODULE: analyze_powerball.py
# PURPOSE: Analyze Powerball draw frequencies and save results.
# VERSION: PowerPlay 2.3.3
# UPDATED: Sprint 2.3.3 – Adds Power Play weighting, improved logging.
# ──────────────────────────────────────────────────────────────
"""
Provides core analysis functions for PowerPlay.

Features:
    • Computes frequency distributions of white and red balls.
    • Supports optional time weighting (recency-based decay).
    • Allows optional Power Play multiplier influence.
    • Saves analysis output as timestamped JSON for reuse in dashboard.

Functions:
    - analyze(draws, last_n=None, weight_window=0, include_pp=False)
    - run(args)
"""

from collections import Counter
from datetime import datetime
from utils.logger import get_logger
from utils.data_io import load_draws, save_json, apply_time_weighting

logger = get_logger(__name__)

# pylint: disable=redefined-outer-name


# ──────────────────────────────────────────────────────────────
# FUNCTION: analyze()
# ──────────────────────────────────────────────────────────────
def analyze(draws, last_n=None, weight_window=0, include_pp=False):
    """
    Compute frequency counts with optional time weighting and Power Play inclusion.

    Args:
        draws (list[dict]): List of draw records.
        last_n (int, optional): Limit analysis to last N draws.
        weight_window (int, optional): Rolling window for time weighting.
        include_pp (bool, optional): Whether to weight draws by Power Play multiplier.

    Returns:
        tuple[Counter, Counter]: (white_counts, red_counts)
    """
    if not draws:
        logger.warning("No draw data provided for analysis.")
        return Counter(), Counter()

    # Limit to most recent draws if specified
    if last_n:
        draws = draws[-last_n:]

    # Apply exponential time weighting if configured
    if weight_window and weight_window > 0:
        draws = apply_time_weighting(draws, window=weight_window)

    white_counts, red_counts = Counter(), Counter()

    # Aggregate frequencies
    for draw in draws:
        weight = draw.get("weight", 1)

        # Optionally boost weighting by Power Play multiplier
        if include_pp and draw.get("power_play"):
            try:
                weight *= int(draw["power_play"])
            except (ValueError, TypeError):
                logger.debug("Invalid Power Play multiplier; skipping weighting.")

        whites = draw.get("whites") or draw.get("white_balls")
        red = draw.get("red") or draw.get("powerball")

        if not whites or red is None:
            continue

        white_counts.update({num: weight for num in whites})
        red_counts.update({red: weight})

    return white_counts, red_counts


# ──────────────────────────────────────────────────────────────
# FUNCTION: run()
# ──────────────────────────────────────────────────────────────
def run(args):
    """
    Execute the Powerball frequency analysis workflow.

    Args:
        args (Namespace-like): Object with:
            - last (int): Number of draws to include.
            - weight_window (int): Time weighting window.
            - include_pp (bool): Whether to include Power Play multiplier.
    """
    include_pp = getattr(args, "include_pp", False)
    last_n = getattr(args, "last", 20)
    weight_window = getattr(args, "weight_window", 0)

    logger.info("Running analysis (include Power Play = %s)", include_pp)

    draws = load_draws()
    if not draws:
        logger.error("No valid draw data found. Exiting analysis.")
        return

    whites, reds = analyze(
        draws, last_n=last_n, weight_window=weight_window, include_pp=include_pp
    )

    # Log summaries
    if whites:
        logger.info("[Analyze] Top 5 Hot White Balls:")
        for num, count in whites.most_common(5):
            logger.info("   %2d: %.2f", num, count)

        logger.info("[Analyze] Top 5 Cold White Balls:")
        for num, count in list(reversed(whites.most_common()))[:5]:
            logger.info("   %2d: %.2f", num, count)

    if reds:
        logger.info("[Analyze] Top 5 Hot Red Balls:")
        for num, count in reds.most_common(5):
            logger.info("   %2d: %.2f", num, count)

    # Persist results to JSON
    result = {
        "analyzed_at": datetime.now().isoformat(),
        "last_n": last_n,
        "weight_window": weight_window,
        "include_power_play": include_pp,
        "white_counts": dict(whites),
        "red_counts": dict(reds),
    }

    save_json(result, prefix="analysis")
    logger.info(
        "Analysis complete — saved %d white + %d red counts to new analysis file",
        len(whites),
        len(reds),
    )


# ──────────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from types import SimpleNamespace

    args = SimpleNamespace(last=10, weight_window=5, include_pp=True)
    run(args)
