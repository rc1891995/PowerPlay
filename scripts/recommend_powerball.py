# scripts/recommend_powerball.py

import csv
from collections import Counter
import random


def load_draws(filepath):
    draws = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            draws.append(
                {
                    "whites": [
                        int(row["white_1"]),
                        int(row["white_2"]),
                        int(row["white_3"]),
                        int(row["white_4"]),
                        int(row["white_5"]),
                    ],
                    "red": int(row["red"]),
                }
            )
    return draws


def get_frequencies(draws):
    white_counts, red_counts = Counter(), Counter()
    for d in draws:
        white_counts.update(d["whites"])
        red_counts.update([d["red"]])
    return white_counts, red_counts


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
    filepath = "data/powerball_draws.csv"
    draws = load_draws(filepath)
    white_counts, red_counts = get_frequencies(draws)
    recs = pick_numbers(white_counts, red_counts, mode=args.mode, count=args.count)

    print(f"🎯 [Recommend] Mode: {args.mode} | Generating {args.count} picks\n")
    for i, r in enumerate(recs, 1):
        whites = " ".join(f"{n:02d}" for n in r["whites"])
        print(f"Pick {i}: {whites}  🔴 {r['red']:02d}")
