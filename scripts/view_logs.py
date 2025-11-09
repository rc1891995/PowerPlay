#!/usr/bin/env python3
"""
view_logs.py
Simple CLI helper to view and filter PowerPlay logs.

Usage examples:
    python -m scripts.view_logs
    python -m scripts.view_logs --level ERROR
    python -m scripts.view_logs --tail 50
    python -m scripts.view_logs --contains "Real data fetch complete"
"""

import argparse
from pathlib import Path
import sys
import re

LOG_PATH = Path("logs/powerplay.log")

# --- Simple ANSI colors (optional) ---
COLOR_MAP = {
    "INFO": "\033[92m",  # green
    "ERROR": "\033[91m",  # red
    "WARNING": "\033[93m",
    "RESET": "\033[0m",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="View and filter PowerPlay log activity."
    )
    parser.add_argument(
        "--logfile",
        default=str(LOG_PATH),
        help="Path to log file (default: logs/powerplay.log)",
    )
    parser.add_argument(
        "--level",
        choices=["INFO", "ERROR", "WARNING"],
        help="Filter by log level.",
    )
    parser.add_argument(
        "--contains",
        help="Show only lines containing this text.",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=50,
        help="Show only the last N lines (default: 50).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in output.",
    )
    return parser.parse_args()


def colorize(line: str, no_color: bool = False) -> str:
    if no_color:
        return line
    # detect level in line
    m = re.search(r"\[(INFO|ERROR|WARNING)\]", line)
    if not m:
        return line
    level = m.group(1)
    color = COLOR_MAP.get(level, "")
    reset = COLOR_MAP["RESET"]
    return f"{color}{line}{reset}"


def main() -> None:
    args = parse_args()
    log_file = Path(args.logfile)

    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        sys.exit(1)

    # read all lines
    lines = log_file.read_text(encoding="utf-8").splitlines()

    # tail
    if args.tail and args.tail > 0:
        lines = lines[-args.tail :]

    # filter by level
    if args.level:
        level_pat = f"[{args.level}]"
        lines = [ln for ln in lines if level_pat in ln]

    # filter by text
    if args.contains:
        lines = [ln for ln in lines if args.contains in ln]

    # print
    if not lines:
        print("⚠️ No log lines matched your filters.")
        return

    for line in lines:
        print(colorize(line, args.no_color))


if __name__ == "__main__":
    main()
