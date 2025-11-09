#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────
# MODULE: view_logs.py
# PURPOSE: Simple CLI helper to view and filter PowerPlay logs.
# UPDATED: Sprint 2.3.4 – Adds improved filters, color handling, and UX polish.
# ──────────────────────────────────────────────────────────────
"""
View and filter PowerPlay logs directly from the CLI.

Usage examples:
    python -m scripts.view_logs
    python -m scripts.view_logs --level ERROR
    python -m scripts.view_logs --tail 50
    python -m scripts.view_logs --contains "Real data fetch complete"
    python -m scripts.view_logs --since "2025-11-01"
"""

# ──────────────────────────────────────────────────────────────
# Standard Library Imports
# ──────────────────────────────────────────────────────────────
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────
LOG_PATH = Path("logs/powerplay.log")

COLOR_MAP = {
    "INFO": "\033[92m",  # green
    "WARNING": "\033[93m",  # yellow
    "ERROR": "\033[91m",  # red
    "RESET": "\033[0m",
    "HEADER": "\033[95m",  # magenta
}

DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")


# ──────────────────────────────────────────────────────────────
# FUNCTION: parse_args
# PURPOSE: CLI argument parsing
# ──────────────────────────────────────────────────────────────
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
        "--since",
        help="Show only lines logged after this date (YYYY-MM-DD).",
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


# ──────────────────────────────────────────────────────────────
# FUNCTION: colorize
# PURPOSE: Add ANSI color formatting to log lines
# ──────────────────────────────────────────────────────────────
def colorize(line: str, no_color: bool = False) -> str:
    """Apply color highlighting to log lines by severity."""
    if no_color:
        return line
    match = re.search(r"\[(INFO|ERROR|WARNING)\]", line)
    if not match:
        return line
    level = match.group(1)
    color = COLOR_MAP.get(level, "")
    reset = COLOR_MAP["RESET"]
    return f"{color}{line}{reset}"


# ──────────────────────────────────────────────────────────────
# FUNCTION: filter_since
# PURPOSE: Filter log lines after a specific date
# ──────────────────────────────────────────────────────────────
def filter_since(lines: list[str], since_str: str) -> list[str]:
    """Return only log lines after a given date (YYYY-MM-DD)."""
    try:
        cutoff = datetime.strptime(since_str, "%Y-%m-%d")
    except ValueError:
        print(f"⚠️ Invalid date format for --since: {since_str}")
        return lines

    filtered = []
    for line in lines:
        match = DATE_PATTERN.search(line)
        if match:
            try:
                date_val = datetime.strptime(match.group(1), "%Y-%m-%d")
                if date_val >= cutoff:
                    filtered.append(line)
            except Exception:
                continue
    return filtered


# ──────────────────────────────────────────────────────────────
# FUNCTION: main
# PURPOSE: Main log viewing workflow
# ──────────────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()
    log_file = Path(args.logfile)

    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        sys.exit(1)

    # Read log lines safely
    try:
        lines = log_file.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"❌ Failed to read log file: {e}")
        sys.exit(1)

    # Tail last N lines
    if args.tail and args.tail > 0:
        lines = lines[-args.tail :]

    # Filter by level
    if args.level:
        level_pat = f"[{args.level}]"
        lines = [ln for ln in lines if level_pat in ln]

    # Filter by substring
    if args.contains:
        lines = [ln for ln in lines if args.contains.lower() in ln.lower()]

    # Filter by date (--since)
    if args.since:
        lines = filter_since(lines, args.since)

    # Output
    print(f"{COLOR_MAP['HEADER']}──── PowerPlay Log Viewer ────{COLOR_MAP['RESET']}")
    print(f"📄 Source: {log_file}\n")

    if not lines:
        print("⚠️ No log lines matched your filters.")
        return

    for line in lines:
        print(colorize(line, args.no_color))


# ──────────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
