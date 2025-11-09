# utils/scraper_powerball.py
"""
Fetch and cache real Powerball draw data from the official site.
Provides two main functions:
    - fetch_latest_draw(): returns the most recent draw
    - fetch_previous_draws(num): returns last `num` draws
Also includes a CLI mode that saves data to /data/powerball_draws.csv
"""

import re
import time
from pathlib import Path
from typing import Optional, Dict, List

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas as pd

from utils.logger import get_logger

# --- Setup global logger and constants ---
logger = get_logger(__name__)
POWERBALL_URL = "https://www.powerball.com/"
PREVIOUS_RESULTS_URL = "https://www.powerball.com/previous-results"


# --- Utility: safe int parsing for any list of numeric strings ---
def _parse_int_list(text: str) -> List[int]:
    """Parse a string of numbers (space or comma separated) into ints."""
    parts = re.split(r"[,\s]+", text.strip())
    return [int(p) for p in parts if p.isdigit()]


# =============================================================================
#   SCRAPER CORE FUNCTIONS
# =============================================================================


def fetch_latest_draw() -> Optional[Dict]:
    """
    Fetch the most recent Powerball draw from the 'previous results' page.
    Returns a dict with keys: draw_date, white_balls, powerball, power_play.
    """
    logger.info("Fetching latest Powerball results from %s", PREVIOUS_RESULTS_URL)

    try:
        # --- Use a random User-Agent to mimic real browsers ---
        headers = {"User-Agent": UserAgent().random}

        # --- Fetch HTML and wait briefly to avoid rapid hits ---
        resp = requests.get(PREVIOUS_RESULTS_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        time.sleep(1.5)

        soup = BeautifulSoup(resp.text, "lxml")

        # --- find the first result card ---
        first_card = soup.select_one("a.card[href*='draw-result']")
        if not first_card:
            # log part of the title to aid debugging if structure changes
            logger.error("No result cards found. Page title: %s", soup.title)
            return None

        # --- extract draw date from href ---
        href = first_card.get("href", "")
        m = re.search(r"date=(\d{4}-\d{2}-\d{2})", href)
        draw_date = m.group(1) if m else "unknown"

        # --- extract white balls ---
        white_elems = first_card.select("div.white-balls")
        white_nums = [int(el.get_text(strip=True)) for el in white_elems]

        # --- extract red Powerball ---
        pb_elem = first_card.select_one("div.powerball")
        powerball = int(pb_elem.get_text(strip=True)) if pb_elem else None

        # --- extract Power Play multiplier ---
        mult_elem = first_card.select_one("span.multiplier")
        if mult_elem:
            m2 = re.search(r"(\d+)", mult_elem.get_text(strip=True))
            power_play = int(m2.group(1)) if m2 else None
        else:
            power_play = None

        result = {
            "draw_date": draw_date,
            "white_balls": white_nums,
            "powerball": powerball,
            "power_play": power_play,
        }

        logger.info("Fetched draw: %s", result)
        return result

    except Exception as e:
        logger.error("Error parsing latest Powerball page: %s", e)
        return None


def fetch_previous_draws(num: int = 10) -> List[Dict]:
    """
    Fetch the last `num` Powerball draws from the previous-results page.
    Returns a list of dicts with draw_date, white_balls, powerball, power_play.
    """
    logger.info("Fetching last %d Powerball draws from %s", num, PREVIOUS_RESULTS_URL)

    results: List[Dict] = []
    try:
        headers = {"User-Agent": UserAgent().random}
        resp = requests.get(PREVIOUS_RESULTS_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        time.sleep(1.5)
        soup = BeautifulSoup(resp.text, "lxml")

        # --- find all draw cards ---
        cards = soup.select("a.card[href*='draw-result']")[:num]
        if not cards:
            logger.error("No draw cards found. Page title: %s", soup.title)
            return results

        for card in cards:
            # --- extract draw date ---
            href = card.get("href", "")
            m = re.search(r"date=(\d{4}-\d{2}-\d{2})", href)
            draw_date = m.group(1) if m else "unknown"

            # --- extract ball numbers ---
            white_elems = card.select("div.white-balls")
            white_nums = [int(el.get_text(strip=True)) for el in white_elems]

            pb_elem = card.select_one("div.powerball")
            powerball = int(pb_elem.get_text(strip=True)) if pb_elem else None

            mult_elem = card.select_one("span.multiplier")
            if mult_elem:
                m2 = re.search(r"(\d+)", mult_elem.get_text(strip=True))
                power_play = int(m2.group(1)) if m2 else None
            else:
                power_play = None

            results.append(
                {
                    "draw_date": draw_date,
                    "white_balls": white_nums,
                    "powerball": powerball,
                    "power_play": power_play,
                }
            )

        logger.info("Fetched %d previous draws", len(results))
        return results

    except Exception as e:
        logger.error("Error parsing previous-results page: %s", e)
        return results


# =============================================================================
#   CLI MODE – SAVE RESULTS TO CSV CACHE
# =============================================================================
if __name__ == "__main__":
    # --- Fetch both latest and last 50 draws ---
    latest = fetch_latest_draw()
    previous = fetch_previous_draws(50)
    all_draws = [latest] + previous if latest else previous

    if not all_draws:
        print("❌ No draws fetched.")
        exit()

    # --- Normalize and sort data ---
    df = (
        pd.DataFrame(all_draws)
        .drop_duplicates(subset=["draw_date"])
        .sort_values(by="draw_date", ascending=False)
    )

    # --- Ensure /data directory exists ---
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    csv_path = data_dir / "powerball_draws.csv"

    # --- Save with overwrite protection ---
    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        merged = pd.concat([existing, df]).drop_duplicates(subset=["draw_date"])
        merged.to_csv(csv_path, index=False)
        print(f"✅ Updated existing cache with {len(df)} records → {csv_path}")
    else:
        df.to_csv(csv_path, index=False)
        print(f"✅ Created new draw cache → {csv_path}")

    # --- Display preview for confirmation ---
    print(df.head())
