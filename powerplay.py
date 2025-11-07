#!/usr/bin/env python3
"""
PowerPlay CLI - MVP skeleton for Powerball analysis
"""

import argparse
import sys
from scripts import fetch_powerball, analyze_powerball, recommend_powerball


def main():
    parser = argparse.ArgumentParser(
        description="🎲 PowerPlay: Powerball frequency and recommendation tool"
    )

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
        "--weekday", help="Filter draws by weekday (e.g. Mon, Wed, Sat)"
    )
    analyze_parser.add_argument("--month", help="Filter draws by month (e.g. Mar)")
    analyze_parser.add_argument("--since", help="Analyze draws since YYYY-MM-DD")

    # --- Recommend ---
    recommend_parser = subparsers.add_parser(
        "recommend", help="Generate Powerball picks"
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

    args = parser.parse_args()

    # Dispatch based on command
    if args.command == "fetch":
        fetch_powerball.run(args)
    elif args.command == "analyze":
        analyze_powerball.run(args)
    elif args.command == "recommend":
        recommend_powerball.run(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
