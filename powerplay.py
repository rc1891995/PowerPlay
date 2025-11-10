#!/usr/bin/env python3
"""
PowerPlay CLI - MVP skeleton for Powerball analysis
"""

import argparse
import os
import sys

from version import get_version_info


def main():
    """CLI entry point for PowerPlay."""

    parser = argparse.ArgumentParser(
        description="🎲 PowerPlay: Powerball frequency and recommendation tool"
    )

    # --- Global flags ---
    parser.add_argument(
        "--version", action="store_true", help="Show current PowerPlay version"
    )  # <<< moved up

    # --- Subcommands ---
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Fetch ---
    fetch_parser = subparsers.add_parser(
        "fetch", help="Fetch or load Powerball draw data"
    )
    fetch_parser.add_argument(
        "--source",
        choices=["local", "web"],
        default="local",
        help="Data source (default: local CSV file)",
    )

    # --- Analyze ---
    analyze_parser = subparsers.add_parser("analyze", help="Analyze draw frequencies")
    analyze_parser.add_argument(
        "--last", type=int, help="Analyze only the last N draws"
    )
    analyze_parser.add_argument(
        "--weight-window",
        type=int,
        default=0,
        help="Apply time-based weighting over last N draws (0 = no weighting)",
    )
    analyze_parser.add_argument(
        "--weekday", help="Filter draws by weekday (e.g. Mon, Wed, Sat)"
    )
    analyze_parser.add_argument("--month", help="Filter draws by month (e.g. Mar)")
    analyze_parser.add_argument("--since", help="Analyze draws since YYYY-MM-DD")
    analyze_parser.add_argument(
        "--plot", action="store_true", help="Visualize frequency results after analysis"
    )

    # --- Recommend ---
    recommend_parser = subparsers.add_parser(
        "recommend", help="Generate Powerball number recommendations"
    )
    recommend_parser.add_argument(
        "--mode",
        choices=["hot", "cold"],
        default="hot",
        help="Recommendation mode (hot or cold)",
    )
    recommend_parser.add_argument(
        "--count", type=int, default=1, help="Number of picks to generate"
    )
    recommend_parser.add_argument(
        "--exact",
        action="store_true",
        help="Select exact top/bottom numbers instead of random sampling",
    )
    recommend_parser.add_argument(
        "--use-weights",
        action="store_true",
        help="Bias random selection using weighted frequencies",
    )
    recommend_parser.add_argument(
        "--save-picks",
        action="store_true",
        help="Save generated picks to data/recommended_picks.csv",
    )

    # --- Parse arguments ---
    args = parser.parse_args()  # <<< must come before version check

    # --- Handle global flags ---
    if args.version:  # <<< now safe
        print(get_version_info())
        sys.exit(0)

    # --- Dispatch commands ---
    if args.command == "fetch":
        from scripts import fetch_powerball

        fetch_powerball.run(args)

    elif args.command == "analyze":
        from scripts import analyze_powerball

        analyze_powerball.run(args)

        # Optional plotting
        if getattr(args, "plot", False):
            from scripts import analyze_visuals

            data_dir = "data"
            latest = None
            for fname in sorted(os.listdir(data_dir), reverse=True):
                if fname.startswith("analysis_") and fname.endswith(".json"):
                    latest = os.path.join(data_dir, fname)
                    break

            if latest and os.path.exists(latest):
                print(f"📊 Opening charts from {latest}")
                analyze_visuals.plot_analysis(latest)
            else:
                print("⚠️  No analysis file found for plotting.")

    elif args.command == "recommend":
        from scripts import recommend_powerball

        recommend_powerball.run(args)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
