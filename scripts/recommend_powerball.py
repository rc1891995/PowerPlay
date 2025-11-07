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
            # weighted random choice based on relative frequencies
            w_nums = [n for n, _ in top_whites]
            w_weights = [freq for _, freq in top_whites]
            whites = sorted(random.choices(w_nums, weights=w_weights, k=5))

            r_nums = [n for n, _ in top_reds]
            r_weights = [freq for _, freq in top_reds]
            red = random.choices(r_nums, weights=r_weights, k=1)[0]
        else:
            whites = sorted(random.sample([n for n, _ in top_whites], 5))
            red = random.choice([n for n, _ in top_reds])
        recommendations.append({"whites": whites, "red": red})
    return recommendations


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
    for i, r in enumerate(recs, 1):
        whites = " ".join(f"{n:02d}" for n in r["whites"])
        print(f"Pick {i}: {whites}  🔴 {r['red']:02d}")
        print(
            "\n✨  Tip: use '--exact' for deterministic top/bottom picks "
            "or '--use-weights' for probability-biased random draws."
        )
