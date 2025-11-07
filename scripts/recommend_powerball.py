# scripts/recommend_powerball.py
"""
Generate Powerball number recommendations.
"""

import random
from utils.data_io import load_draws, count_frequencies


def pick_numbers(white_counts, red_counts, mode="hot", count=1):
    """Return recommended numbers based on mode ('hot' or 'cold')."""
    if mode == "hot":
        top_whites = [n for n, _ in white_counts.most_common(20)]
        top_reds = [n for n, _ in red_counts.most_common(10)]
    elif mode == "cold":
        top_whites = [n for n, _ in white_counts.most_common()[:-21:-1]]
        top_reds = [n for n, _ in red_counts.most_common()[:-11:-1]]
    else:
        raise ValueError("Invalid mode")

    recommendations = []
    for _ in range(count):
        whites = sorted(random.sample(top_whites, 5))
        red = random.choice(top_reds)
        recommendations.append({"whites": whites, "red": red})
    return recommendations


def run(args):
    """Main CLI entrypoint for recommendation generation."""
    draws = load_draws()
    white_counts, red_counts = count_frequencies(draws)
    recs = pick_numbers(white_counts, red_counts, mode=args.mode, count=args.count)

    print(f"🎯 [Recommend] Mode: {args.mode} | Generating {args.count} picks\n")
    for i, r in enumerate(recs, 1):
        whites = " ".join(f"{n:02d}" for n in r["whites"])
        print(f"Pick {i}: {whites}  🔴 {r['red']:02d}")
