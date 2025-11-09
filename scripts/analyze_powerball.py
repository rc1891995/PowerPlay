# ──────────────────────────────────────────────────────────────
# MODULE: analyze_powerball.py
# PURPOSE: Analyze Powerball draw frequencies and save results.
# ──────────────────────────────────────────────────────────────

"""
Module: analyze_powerball.py
Description:
    Provides functions to analyze Powerball draw frequencies.
    Supports optional time weighting and limited draw windows,
    producing both frequency statistics and JSON output for the
    PowerPlay dashboard.

Functions:
    - analyze(draws, last_n=None, weight_window=0)
        Computes white/red ball frequency counts with optional
        time weighting.
    - run(args)
        Executes analysis workflow and saves results as JSON.
"""

from collections import Counter
from datetime import datetime
from utils.logger import get_logger

logger = get_logger()

from utils.data_io import load_draws, save_json, apply_time_weighting

# pylint: disable=redefined-outer-name


def analyze(draws, last_n=None, weight_window=0):
    """
    Compute frequency counts with optional time weighting.

    Args:
        draws (list[dict]): List of draw records.
        last_n (int, optional): Limit analysis to last N draws.
        weight_window (int, optional): Rolling window for time weighting.

    Returns:
        tuple[Counter, Counter]: White ball and red ball frequency counters.
    """
    # Limit to most recent draws if specified
    if last_n:
        draws = draws[-last_n:]

    # Apply exponential time weighting if configured
    if weight_window and weight_window > 0:
        draws = apply_time_weighting(draws, window=weight_window)

    white_counts, red_counts = Counter(), Counter()

    # Aggregate frequencies with optional weighting
    for draw in draws:
        weight = draw.get("weight", 1)
        white_counts.update({num: weight for num in draw["whites"]})
        red_counts.update({draw["red"]: weight})

    return white_counts, red_counts


def run(args):
    """
    Execute the Powerball frequency analysis workflow.

    Args:
        args (Namespace-like): Object containing attributes:
            - last (int): Number of draws to include.
            - weight_window (int): Time weighting window.
    """
    draws = load_draws()
    whites, reds = analyze(draws, last_n=args.last, weight_window=args.weight_window)

    # Display summary in console
    logger.info("[Analyze] Top 5 Hot White Balls:")
    for num, count in whites.most_common(5):
        logger.info("   %2d: %.2f", num, count)

    logger.info("[Analyze] Top 5 Cold White Balls:")
    for num, count in list(reversed(whites.most_common()))[:5]:
        logger.info("   %2d: %.2f", num, count)

    logger.info("[Analyze] Top 5 Hot Red Balls:")
    for num, count in reds.most_common(5):
        logger.info("   %2d: %.2f", num, count)

    # Persist results to JSON
    result = {
        "analyzed_at": datetime.now().isoformat(),
        "last_n": args.last,
        "weight_window": args.weight_window,
        "white_counts": whites,
        "red_counts": reds,
    }

    save_json(result, prefix="analysis")
    logger.info(
        "Analysis complete — saved %d white + %d red counts to new analysis file",
        len(whites),
        len(reds),
    )


if __name__ == "__main__":
    from types import SimpleNamespace

    args = SimpleNamespace(last=10, weight_window=5)
    run(args)
