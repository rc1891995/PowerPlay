# utils/auto_update.py
"""
===============================================================================
 PowerPlay Module: auto_update
-------------------------------------------------------------------------------
 Orchestrates automatic synchronization of draw data on application startup.

 Responsibilities:
   • Verify local Powerball CSV cache
   • Compare most recent local vs. latest web draw
   • Append new draw if missing
   • Persist all draws to the SQLite database

 Imported by:
   powerplay.py → auto_fetch_powerball()

 Author:  PowerPlay Development Team
 Version: 2.5.0-alpha
===============================================================================
"""

from utils.scraper_powerball import (
    fetch_latest_draw,
    load_cached_draws,
    append_draw_to_csv,
    CSV_PATH,
)
from utils.db_io import insert_draw, init_db
from utils.logger import get_logger

# =============================================================================
#   GLOBALS AND LOGGER
# =============================================================================
logger = get_logger(__name__)


# =============================================================================
#   POWERBALL AUTO-FETCH LOGIC
# =============================================================================
def auto_fetch_powerball() -> None:
    """
    Ensure local Powerball data is current by comparing the latest local draw
    to the most recent draw from the official Powerball site.  If new,
    append to CSV and insert into SQLite database.
    """
    try:
        # Ensure DB tables exist before writing
        init_db()

        cached = load_cached_draws(CSV_PATH)
        latest_remote = fetch_latest_draw()

        if not latest_remote:
            msg = "⚠️  Could not fetch latest Powerball draw from web."
            logger.warning(msg)
            print(msg)
            return

        remote_date = latest_remote.get("draw_date")

        if not cached:
            print("📄 No local Powerball data found. Initializing CSV and DB.")
            append_draw_to_csv(latest_remote, CSV_PATH)
            insert_draw(latest_remote)
            return

        latest_local = cached[-1]
        local_date = latest_local.get("draw_date")

        if remote_date and remote_date != local_date:
            print(f"🆕 New Powerball draw found ({remote_date}). Appending...")
            append_draw_to_csv(latest_remote, CSV_PATH)
            insert_draw(latest_remote)
        else:
            print("✅ Powerball draws are up to date.")

    except Exception as e:
        logger.error("Auto-fetch failed: %s", e)
        print(f"❌ Auto-fetch failed: {e}")
