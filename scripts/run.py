"""
Master runner for PowerPlay.
Runs:
1. Backfill (full refresh)
2. Pattern analysis
3. Dashboard startup
"""

import subprocess
import sys
from pathlib import Path


def run_cmd(description, cmd_list):
    print(f"\n🚀 {description}...")
    try:
        subprocess.run(cmd_list, check=True)
        print(f"✅ {description} complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        sys.exit(1)


def main():
    project_root = Path(__file__).resolve().parents[1]
    print("========================================")
    print("  POWERPLAY: MASTER RUN SCRIPT")
    print("========================================")
    print(f"Project Root: {project_root}")

    # 1) BACKFILL DATA
    run_cmd(
        "Refreshing Powerball draw data",
        [sys.executable, "-m", "scripts.backfill_powerball"],
    )

    # 2) ANALYZE PATTERNS
    run_cmd(
        "Running extended analysis",
        [sys.executable, "-m", "scripts.analyze_patterns_extended"],
    )

    # 3) START STREAMLIT DASHBOARD
    print("\n📊 Launching dashboard (this will not block other tasks)...")
    print("Use Ctrl+C to stop Streamlit when done.")
    subprocess.run(["streamlit", "run", "scripts/dashboard_app.py"])


if __name__ == "__main__":
    main()
