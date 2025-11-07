# scripts/analyze_powerball.py

import csv
from collections import Counter
from datetime import datetime


def load_draws(filepath):
    draws = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            draws.append(
                {
                    "date": datetime.strptime(row["date"], "%Y-%m-%d"),
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


def analyze(draws, last_n=None):
    if last_n:
        draws = draws[-last_n:]
    white_counts, red_counts = Counter(), Counter()
    for d in draws:
        white_counts.update(d["whites"])
        red_counts.update([d["red"]])
    return white_counts, red_counts


def run(args):
    """Analyze Powerball draw frequencies"""
    filepath = "data/powerball_draws.csv"
    draws = load_draws(filepath)
    whites, reds = analyze(draws, last_n=args.last)
    print("📊 [Analyze] Frequency of white balls (top 10):")
    for num, count in whites.most_common(10):
        print(f"   {num:2d}: {count}")
    print("🎯 [Analyze] Frequency of red balls:")
    for num, count in reds.most_common():
        print(f"   {num:2d}: {count}")
