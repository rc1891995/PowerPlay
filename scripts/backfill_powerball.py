"""
Fetch ONLY the latest Powerball draw and append it to data/powerball_draws.csv.
"""

import requests
from utils.data_io import append_draw_to_csv
from utils.logger import get_logger

logger = get_logger(__name__)

NY_API_URL = (
    "https://data.ny.gov/resource/d6yy-54nr.json?$limit=1&$order=draw_date DESC"
)


def fetch_latest_draw():
    logger.info("Fetching the latest Powerball draw from NY Open Data API")
    r = requests.get(NY_API_URL, timeout=10)

    if r.status_code != 200:
        raise RuntimeError(f"NY API request failed: {r.status_code}")

    data = r.json()
    if not data:
        raise RuntimeError("No draw returned from NY API")

    d = data[0]

    # Parse NY style "winning_numbers": "05 27 36 45 54 10"
    nums = [int(x) for x in d["winning_numbers"].split()]

    whites = nums[:5]
    red = nums[5]

    multiplier = d.get("multiplier")
    try:
        pp = int(multiplier)
    except:
        pp = 1

    draw = {
        "draw_date": d["draw_date"],
        "white_balls": whites,
        "powerball": red,
        "power_play": pp,
    }

    logger.info(f"Latest draw = {draw}")
    return draw


def main():
    draw = fetch_latest_draw()
    append_draw_to_csv(draw)
    logger.info(f"Appended draw {draw['draw_date']} to CSV.")


if __name__ == "__main__":
    main()
