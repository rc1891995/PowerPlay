# scripts/recommend_powerball.py
"""
Generate Powerball number recommendations.
"""


from utils.data_io import load_draws, count_frequencies


# ──────────────────────────────────────────────────────────────
# FUNCTION: pick_numbers
# PURPOSE: Generate Powerball recommendations (weighted or uniform)
# ──────────────────────────────────────────────────────────────
def pick_numbers(
    white_counts, red_counts, mode="hot", count=1, exact=False, use_weights=False
):
    if mode == "hot":
        sorted_whites = white_counts.most_common()
        sorted_reds = red_counts.most_common()
    elif mode == "cold":
        sorted_whites = list(reversed(white_counts.most_common()))
        sorted_reds = list(reversed(red_counts.most_common()))
    else:
        raise ValueError("Invalid mode")

    if exact:
        whites = sorted([n for n, _ in sorted_whites[:5]])
        red = sorted_reds[0][0]
        return [{"whites": whites, "red": red}]

    # Build selection pools
    top_whites = sorted_whites[:20]
    top_reds = sorted_reds[:10]

    import random

    recommendations = []
    for _ in range(count):
        if use_weights:
            # Weighted, unique sample (no duplicates)
            w_nums = [n for n, _ in top_whites]
            w_weights = [freq for _, freq in top_whites]
            whites = sorted(random.choices(w_nums, weights=w_weights, k=20))
            whites = sorted(list(dict.fromkeys(whites))[:5])  # deduplicate, keep order
            if len(whites) < 5:  # ensure 5 unique
                extras = [n for n in w_nums if n not in whites]
                whites += random.sample(extras, 5 - len(whites))

            r_nums = [n for n, _ in top_reds]
            r_weights = [freq for _, freq in top_reds]
            red = random.choices(r_nums, weights=r_weights, k=1)[0]
        else:
            whites = sorted(random.sample([n for n, _ in top_whites], 5))
            red = random.choice([n for n, _ in top_reds])

        recommendations.append({"whites": whites, "red": red})

    return recommendations


# ──────────────────────────────────────────────────────────────
# COLORS
# ──────────────────────────────────────────────────────────────
def colorize(num, hot_threshold, cold_threshold):
    """Return colored string based on frequency."""
    if num >= hot_threshold:
        return f"\033[91m{num:02d}\033[0m"  # 🔥 red/hot
    elif num <= cold_threshold:
        return f"\033[94m{num:02d}\033[0m"  # 🧊 blue/cold
    return f"\033[92m{num:02d}\033[0m"  # 💚 neutral


def run(args):
    """Main CLI entrypoint for recommendation generation."""
    draws = load_draws()
    white_counts, red_counts = count_frequencies(draws)
    recs = pick_numbers(
        white_counts,
        red_counts,
        mode=args.mode,
        count=args.count,
        exact=args.exact,
        use_weights=args.use_weights,
    )

    print(f"🎯 [Recommend] Mode: {args.mode} | Generating {args.count} picks\n")
    for i, r in enumerate(recs, start=1):
        whites_str = " ".join(colorize(n, 50, 5) for n in r["whites"])

    print(f"\nPick {i}: {whites_str}  🔴 {r['red']:02d}")

    if args.use_weights:
        total_w = sum(freq for _, freq in white_counts.most_common(20))
        top_ball, top_freq = white_counts.most_common(1)[0]
        bias_pct = (top_freq / total_w) * 100
    print(
        f"📈  Weighted bias summary: hottest ball {top_ball} accounts for {bias_pct:.1f}% of selection weight."
    )

    # Show hint once after all picks
    print(
        "\n✨  Tip: use '--exact' for deterministic top/bottom picks "
        "or '--use-weights' for probability-biased random draws.\n"
    )

    # ──────────────────────────────────────────────────────────────


# FUNCTION: run
# PURPOSE: Execute the recommendation workflow
# ──────────────────────────────────────────────────────────────
def run(args):
    """Run the PowerPlay recommendation workflow."""
    from utils.data_io import load_draws, count_frequencies
    from collections import Counter

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

    # ──────────────────────────────────────────────────────────────
    # Display Picks (with optional color)
    # ──────────────────────────────────────────────────────────────
    for i, r in enumerate(recs, start=1):
        whites_str = " ".join(f"{n:02d}" for n in r["whites"])
        print(f"Pick {i}: {whites_str}  🔴 {r['red']:02d}")

    # Print a single hint once at the end
    print(
        "\n✨  Tip: use '--exact' for deterministic top/bottom picks "
        "or '--use-weights' for probability-biased random draws.\n"
    )

    # ──────────────────────────────────────────────────────────────
    # Weighted bias summary (if applicable)
    # ──────────────────────────────────────────────────────────────
    if args.use_weights:
        total_w = sum(freq for _, freq in white_counts.most_common(20))
        top_ball, top_freq = white_counts.most_common(1)[0]
        bias_pct = (top_freq / total_w) * 100
        print(
            f"📈  Weighted bias summary: hottest ball {top_ball} "
            f"accounts for {bias_pct:.1f}% of selection weight."
        )

    # ──────────────────────────────────────────────────────────────
    # Optional: Save picks to CSV
    # ──────────────────────────────────────────────────────────────
    if args.save_picks:
        import csv, os

        out_path = os.path.join("data", "recommended_picks.csv")
        os.makedirs("data", exist_ok=True)
        with open(out_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for r in recs:
                writer.writerow(r["whites"] + [r["red"]])
        print(f"💾  Saved picks to {out_path}")
