"""
Quick runner for PowerPlay.
Runs:
1. Fetches the latest Powerball draw (no full refresh)
2. Appends to CSV
3. Runs analysis
4. Launches Streamlit dashboard
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
    print("============================================")
    print("  POWERPLAY: QUICK RUN MODE")
    print("============================================")
    print(f"Project Root: {project_root}")

    # 1) Fetch ONLY the latest Powerball draw
    run_cmd(
        "Fetching latest Powerball draw",
        [sys.executable, "-m", "scripts.backfill_powerball"],
    )

    # 2) Run extended analysis
    run_cmd(
        "Running extended statistical analysis",
        [sys.executable, "-m", "scripts.analyze_patterns_extended"],
    )

    # 3) Launch Streamlit dashboard
    print("\n📊 Launching dashboard... (Ctrl+C to exit)")
    subprocess.run(["streamlit", "run", "scripts/dashboard_app.py"])


if __name__ == "__main__":
    main()
