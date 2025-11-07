# scripts/analyze_powerball.py
"""
Analyze Powerball draw frequencies and save results.
"""

from collections import Counter
from datetime import datetime

from utils.data_io import load_draws, count_frequencies, save_json, apply_time_weighting


def analyze(draws, last_n=None, weight_window=0):
    """Compute frequency counts with optional time weighting."""
    if last_n:
        draws = draws[-last_n:]

    if weight_window and weight_window > 0:
        draws = apply_time_weighting(draws, window=weight_window)

    white_counts, red_counts = Counter(), Counter()
    for d in draws:
        weight = d.get("weight", 1)
        white_counts.update({num: weight for num in d["whites"]})
        red_counts.update({d["red"]: weight})
    return white_counts, red_counts


def run(args):
    draws = load_draws()
    whites, reds = analyze(draws, last_n=args.last, weight_window=args.weight_window)

    print("\n📊 [Analyze] Top 5 Hot White Balls:")
    for num, count in whites.most_common(5):
        print(f"   {num:2d}: {count:.2f}")

    print("\n🥶 [Analyze] Top 5 Cold White Balls:")
    for num, count in list(reversed(whites.most_common()))[:5]:
        print(f"   {num:2d}: {count:.2f}")

    print("\n🎯 [Analyze] Top 5 Hot Red Balls:")
    for num, count in reds.most_common(5):
        print(f"   {num:2d}: {count:.2f}")

    result = {
        "analyzed_at": datetime.now().isoformat(),
        "last_n": args.last,
        "weight_window": args.weight_window,
        "white_counts": whites,
        "red_counts": reds,
    }
    save_json(result, prefix="analysis")
