"""
Populate full historical Powerball dataset (2015–present).
Pulls paginated archive pages from powerball.com using the
adaptive selector scraper in utils.scraper_powerball.

Writes all results to:
  • data/powerball_draws.csv
  • data/powerplay.db (SQLite)

This script is intentionally conservative with rate-limiting
to avoid powerball.com soft-blocking or introducing captchas.
"""

import time
from utils.logger import get_logger
from utils.data_io import append_draw_to_csv, CSV_PATH
from utils.db_io import insert_draw, init_db
from utils.scraper_powerball import fetch_draws_from_page

logger = get_logger(__name__)


# ──────────────────────────────────────────────────────────────
# MAIN LOGIC
# ──────────────────────────────────────────────────────────────
def real_backfill(max_pages: int = 50, throttle: float = 2.0):
    """
    Fetch historical Powerball results page-by-page.

    Args:
        max_pages (int): Maximum number of archive pages to pull.
                         Each page typically contains up to 50 draws.
        throttle (float): Seconds to sleep between page fetches.

    Behavior:
        - Stops automatically when a page returns 0 draws.
        - Inserts into both CSV and SQLite.
        - Deduplicates automatically via each layer’s logic.
    """

    # Initialize database
    init_db()
    logger.info("🧾 Starting REAL historical Powerball backfill")

    total_inserted = 0

    for page in range(1, max_pages + 1):

        draws = fetch_draws_from_page(page)

        # If zero results, stop — we reached the end
        if not draws:
            logger.info(f"Stopping at page {page} (no more results)")
            break

        logger.info(f"📄 Page {page}: ingesting {len(draws)} draw(s)")

        # Process each draw
        for draw in draws:
            try:
                append_draw_to_csv(draw, CSV_PATH)
                insert_draw(draw)
                total_inserted += 1
            except Exception as e:
                logger.error(f"❌ Failed to save draw {draw.get('draw_date')}: {e}")

        # Throttle to avoid suspicion
        time.sleep(throttle)

    logger.info(
        f"✅ Historical ingestion complete ({total_inserted} total draws inserted)"
    )


# ──────────────────────────────────────────────────────────────
# STANDALONE EXECUTION
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    real_backfill()
