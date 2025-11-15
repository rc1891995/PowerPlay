# utils/db_io.py
from sqlalchemy import create_engine, Column, Integer, String, Date, JSON, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)
DB_PATH = "data/powerplay.db"

Base = declarative_base()


class Draw(Base):
    __tablename__ = "draws"
    id = Column(Integer, primary_key=True, autoincrement=True)
    draw_date = Column(String, unique=True, index=True)
    white_balls = Column(JSON)
    powerball = Column(Integer)
    power_play = Column(Integer)


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Session = sessionmaker(bind=engine)


def init_db():
    """Create the SQLite DB and tables if not present."""
    Base.metadata.create_all(engine)
    logger.info("Initialized SQLite database at %s", DB_PATH)


def insert_draw(draw: dict):
    """Insert a draw record into the SQLite DB, skipping duplicates."""
    try:
        session = Session()
        draw_date = draw.get("draw_date")
        if not draw_date:
            logger.warning("Skipping draw with no date.")
            return

        # Prevent duplicates
        existing = session.query(Draw).filter_by(draw_date=draw_date).first()
        if existing:
            logger.info("Skipping duplicate draw %s", draw_date)
            return

        record = Draw(
            draw_date=draw_date,
            white_balls=draw.get("white_balls"),
            powerball=draw.get("powerball"),
            power_play=draw.get("power_play"),
        )
        session.add(record)
        session.commit()
        logger.info("Inserted draw %s into database", draw_date)

    except Exception as e:
        logger.error("Failed to insert draw into database: %s", e)
        session.rollback()
    finally:
        session.close()
