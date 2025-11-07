# scripts/fetch_powerball.py


def run(args):
    """Fetch Powerball draw data (local or web)"""
    if args.source == "local":
        print("📁 [Fetch] Loading Powerball draws from local CSV...")
    else:
        print("🌐 [Fetch] Fetching latest Powerball draws from web (coming soon)...")
