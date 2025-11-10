# utils/db_io.py
"""
===============================================================================
 PowerPlay Module: db_io
-------------------------------------------------------------------------------
 Provides local database persistence for PowerPlay draw data using SQLite
 and SQLAlchemy ORM.

 Primary Responsibilities:
   • Initialize the local database (powerplay.db)
   • Define ORM models (Draw table)
   • Insert new draw records
   • Retrieve existing draws for analysis

 Future Expansion:
   - Support multiple game tables (MegaMillions, ColoradoLotto)
   - Integrate with cloud databases (RDS, DynamoDB)
   - Sync via CI/CD workflows

 Author:  PowerPlay Development Team
 Version: 2.5.0-alpha
===============================================================================
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import Column, Date, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from utils.logger import get_logger

# =============================================================================
#   GLOBALS AND LOGGER
# =============================================================================
logger = get_logger(__name__)
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "powerplay.db"

Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)

# =============================================================================
#   ORM MODEL DEFINITIONS
# =============================================================================
class Draw(Base):
    """ORM model representing a single Powerball draw."""
    __tablename__ = "draws"

    id = Column(Integer, primary_key=True, autoincrement=True)
    draw_date = Column(Date, unique=True, nullable=False)
    white_balls = Column(String, nullable=False)
    powerball = Column(Integer, nullable=False)
    power_play = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Draw(date={self.draw_date}, "
            f"white_balls='{self.white_balls}', "
            f"powerball={self.powerball}, power_play={self.power_play})>"
        )


# =============================================================================
#   CORE DATABASE FUNCTIONS
# =============================================================================
def init_db() -> None:
    """Initialize the SQLite database and create tables if not present."""
    try:
        Base.metadata.create_all(engine)
        logger.info("Initialized SQLite database at %s", DB_PATH)
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        raise


def insert_draw(draw: Dict) -> None:
    """Insert a single draw record into the database."""
    session = SessionLocal()
    try:
        # Ensure date object type
        draw_date = datetime.strptime(draw["draw_date"], "%Y-%m-%d").date()
        new_draw = Draw(
            draw_date=draw_date,
            white_balls=str(draw.get("white_balls")),
            powerball=draw.get("powerball"),
            power_play=draw.get("power_play"),
        )
        session.add(new_draw)
        session.commit()
        logger.info("Inserted draw %s into database", draw["draw_date"])
    except Exception as e:
        session.rollback()
        logger.error("Failed to insert draw: %s", e)
    finally:
        session.close()


def load_draws(limit: Optional[int] = None) -> List[Draw]:
    """Load draw records from the database (optionally limited)."""
    session = SessionLocal()
    try:
        query = session.query(Draw).order_by(Draw.draw_date.desc())
        if limit:
            query = query.limit(limit)
        results = query.all()
        logger.info("Loaded %d draws from database", len(results))
        return results
    except Exception as e:
        logger.error("Failed to load draws: %s", e)
        return []
    finally:
        session.close()
