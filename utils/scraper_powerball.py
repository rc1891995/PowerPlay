"""
Scraper for Powerball official results pages.

Provides:
    - fetch_latest_draw()
    - fetch_draws_from_page(page)

Handles:
    - Multiple site layout changes (2023–2025)
    - Adaptive selectors
    - Safe parsing for white balls, PB, and power play
"""

import re
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from utils.logger import get_logger

logger = get_logger(__name__)

PREVIOUS_RESULTS_URL = "https://www.powerball.com/previous-results"


# ──────────────────────────────────────────────────────────────
# Helper: parse any whitespace / comma-separated numbers
# ──────────────────────────────────────────────────────────────
def _parse_int_list(text: str) -> List[int]:
    parts = re.split(r"[,\s]+", text.strip())
    return [int(p) for p in parts if p.isdigit()]


# ──────────────────────────────────────────────────────────────
# Fetch the latest draw
# ──────────────────────────────────────────────────────────────
def fetch_latest_draw() -> Optional[Dict]:
    """
    Scrape the latest draw from the previous-results page.

    Uses aggressive multi-selector logic.
    """

    from datetime import datetime, timedelta

    logger.info("Fetching latest Powerball results from %s", PREVIOUS_RESULTS_URL)

    # Prevent hammering Powerball.com
    cache_flag = Path("data/last_fetch.txt")
    now = datetime.now()
    if cache_flag.exists():
        last = datetime.fromtimestamp(cache_flag.stat().st_mtime)
        if now - last < timedelta(hours=6):
            logger.info("Skipping fetch (cooldown < 6 hours).")
            return None

    try:
        headers = {"User-Agent": UserAgent().random}
        resp = requests.get(PREVIOUS_RESULTS_URL, headers=headers, timeout=10)
        resp.raise_for_status()

        time.sleep(0.5)
        soup = BeautifulSoup(resp.text, "lxml")

        # Layer 1 — new layout (2024–2025)
        card = soup.select_one("a.card[href*='draw-result']")

        # Layer 2 — legacy layout
        if not card:
            card = soup.select_one("a[href*='/numbers/']")

        # Layer 3 — fallback
        if not card:
            card = soup.select_one("div.result-item a")

        # Hard fail
        if not card:
            logger.error("⚠️ No latest-result card found — layout changed.")
            return None

        href = card.get("href", "")
        date_match = re.search(r"date=(\d{4}-\d{2}-\d{2})", href)
        draw_date = date_match.group(1) if date_match else None

        # White balls (several layouts use different tags)
        white_elems = (
            card.select("div.white-balls span")
            or card.select("span.white-balls")
            or card.select("div.white-balls")
        )
        whites = [
            int(el.get_text(strip=True))
            for el in white_elems
            if el.get_text(strip=True).isdigit()
        ]

        # Powerball
        pb_elem = (
            card.select_one("div.powerball span")
            or card.select_one("span.powerball")
            or card.select_one("div.powerball")
        )
        powerball = int(pb_elem.get_text(strip=True)) if pb_elem else None

        # PowerPlay multiplier
        mult_elem = (
            soup.select_one("span.multiplier")
            or soup.select_one("span.power-play")
            or soup.select_one("div.power-play")
        )
        power_play = None
        if mult_elem:
            m = re.search(r"(\d+)", mult_elem.get_text(strip=True))
            power_play = int(m.group(1)) if m else None

        data = {
            "draw_date": draw_date,
            "white_balls": whites,
            "powerball": powerball,
            "power_play": power_play,
        }

        logger.info("Latest draw: %s", data)
        cache_flag.touch()
        return data

    except Exception as e:
        logger.error("❌ Error scraping latest draw: %s", e)
        return None


# ──────────────────────────────────────────────────────────────
# Fetch historical paginated results
# ──────────────────────────────────────────────────────────────
def fetch_draws_from_page(page: int) -> List[Dict]:
    """
    Scrape one historical page of draws from the paginated archive.

    Returns list of draw dicts.
    """

    url = f"https://www.powerball.com/previous-results?per_page=50&page={page}"
    logger.info(f"Fetching historical page {page}: {url}")

    try:
        headers = {"User-Agent": UserAgent().random}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # New layout result cards
        cards = soup.select("a.card[href*='draw-result']")

        # If that fails, try older layouts
        if not cards:
            cards = soup.select("a[href*='/numbers/']")

        if not cards:
            cards = soup.select("div.result-item a")

        # If STILL empty → no results
        if not cards:
            logger.warning("⚠️ No cards found on page — probably end of archive.")
            return []

        results = []

        for card in cards:
            # Extract date
            href = card.get("href", "")
            date_match = re.search(r"date=(\d{4}-\d{2}-\d{2})", href)
            draw_date = date_match.group(1) if date_match else None
            if not draw_date:
                continue

            # Extract whites
            white_elems = (
                card.select("div.white-balls span")
                or card.select("span.white-balls")
                or card.select("div.white-balls")
            )
            whites = [
                int(el.get_text(strip=True))
                for el in white_elems
                if el.get_text(strip=True).isdigit()
            ]

            # Extract PB
            pb_elem = (
                card.select_one("div.powerball span")
                or card.select_one("span.powerball")
                or card.select_one("div.powerball")
            )
            pb = int(pb_elem.get_text(strip=True)) if pb_elem else None

            # Extract PowerPlay
            mult_elem = card.select_one("span.multiplier") or card.select_one(
                "span.power-play"
            )
            power_play = None
            if mult_elem:
                m = re.search(r"(\d+)", mult_elem.get_text(strip=True))
                power_play = int(m.group(1)) if m else None

            results.append(
                {
                    "draw_date": draw_date,
                    "white_balls": whites,
                    "powerball": pb,
                    "power_play": power_play,
                }
            )

        logger.info(f"📄 Page {page}: Found {len(results)} draws")
        return results

    except Exception as e:
        logger.error(f"❌ Failed to fetch page {page}: {e}")
        return []
