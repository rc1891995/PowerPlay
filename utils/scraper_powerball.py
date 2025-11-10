# utils/scraper_powerball.py
"""
Fetch and cache real Powerball draw data from the official site.

Provides two main functions:
    - fetch_latest_draw(): returns the most recent draw
    - fetch_previous_draws(num): returns last `num` draws

Also includes a CLI mode that saves data to /data/powerball_draws.csv
"""

import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from utils.logger import get_logger

# pylint: disable=duplicate-code

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

# pylint: disable=too-many-locals
def fetch_latest_draw() -> Optional[Dict]:
    """
    Fetch the most recent Powerball draw from the 'previous results' page.

    Returns:
        dict: Keys include draw_date, white_balls, powerball, power_play
    """
    logger.info("Fetching latest Powerball results from %s", PREVIOUS_RESULTS_URL)

    try:
        # --- Use a random User-Agent to mimic real browsers ---
        headers = {"User-Agent": UserAgent().random}
        resp = requests.get(PREVIOUS_RESULTS_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        time.sleep(1.5)

        soup = BeautifulSoup(resp.text, "lxml")

        # --- find the first result card ---
        first_card = soup.select_one("a.card[href*='draw-result']")
        if not first_card:
            logger.error("No result cards found. Page title: %s", soup.title)
            return None

        href = first_card.get("href", "")
        match = re.search(r"date=(\d{4}-\d{2}-\d{2})", href)
        draw_date = match.group(1) if match else "unknown"

        white_elems = first_card.select("div.white-balls")
        white_nums = [int(el.get_text(strip=True)) for el in white_elems]

        pb_elem = first_card.select_one("div.powerball")
        powerball = int(pb_elem.get_text(strip=True)) if pb_elem else None

        mult_elem = first_card.select_one("span.multiplier")
        power_play = None
        if mult_elem:
            match2 = re.search(r"(\d+)", mult_elem.get_text(strip=True))
            power_play = int(match2.group(1)) if match2 else None

        result = {
            "draw_date": draw_date,
            "white_balls": white_nums,
            "powerball": powerball,
            "power_play": power_play,
        }

        logger.info("Fetched draw: %s", result)
        return result

    except (requests.RequestException, ValueError, AttributeError) as e:
        lo
