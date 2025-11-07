# scripts/analyze_powerball.py
"""
Analyze Powerball draw frequencies and save results.
"""

from utils.data_io import load_draws, count_frequencies, save_json
from datetime import datetime


def analyze(draws, last_n=None):
    """Compute frequency counts; supports last N draws."""
    if last_n:
        draws = draws[-last_n:]
    return count_frequencies(draws)


def run(args):
    """Analyze Powerball draw frequencies"""
    draws = load_draws()
    whites, reds = analyze(draws, last_n=args.last)
    print("📊 [Analyze] Frequency of white balls (top 10):")
    for num, count in whites.most_common(10):
        print(f"   {num:2d}: {count}")
    print("🎯 [Analyze] Frequency of red balls:")
    for num, count in reds.most_common():
        print(f"   {num:2d}: {count}")

    result = {
        "analyzed_at": datetime.now().isoformat(),
        "last_n": args.last,
        "white_counts": whites,
        "red_counts": reds,
    }
    save_json(result, prefix="analysis")
