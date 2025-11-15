"""
scripts/backfill_powerball.py
---------------------------------
Populate PowerPlay with simulated or real historical draws.
Dual-writes to CSV and SQLite DB.
"""

from utils.logger import get_logger
from utils.data_io import append_draw_to_csv, CSV_PATH
from utils.db_io import insert_draw, init_db
import random, time

logger = get_logger(__name__)


def backfill_historical_draws():
    """Simulated historical backfill (to be replaced with real archive pull)."""
    init_db()
    logger.info("🧾 Starting historical backfill (simulated placeholder)")

    total_inserted = 0
    for year in range(2015, 2025):
        for _ in range(random.randint(20, 40)):  # ~20–40 draws per year
            draw = {
                "draw_date": f"{year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "white_balls": sorted(random.sample(range(1, 70), 5)),
                "powerball": random.randint(1, 26),
                "power_play": random.choice([None, 2, 3, 4, 5]),
            }
            append_draw_to_csv(draw, CSV_PATH)
            insert_draw(draw)
            total_inserted += 1
        logger.info("✅ Year %s complete", year)
        time.sleep(0.05)

    logger.info(
        "✅ Historical backfill complete (%d total draws inserted)", total_inserted
    )


if __name__ == "__main__":
    backfill_historical_draws()
