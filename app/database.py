import os
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy import inspect
from dotenv import load_dotenv
import logging
from redis import Redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

engine = create_engine(DATABASE_URL, echo=True)
redis_client = Redis.from_url(REDIS_URL)

def init_db():
    try:
        inspector = inspect(engine)
        # LIST OF ALL TABLES
        existing_tables = inspector.get_table_names()

        # NO NEED TO CREATE IF IT IS ALREADY EXIST
        if not existing_tables:
            SQLModel.metadata.create_all(engine)
            logger.info("Tables created successfully")
        else:
            logger.info("Tables already exist, skipping creation")
    except Exception as e:
        logger.error(f"Error in initializing the database: {e}")
        raise

def get_db():
    try:
        with Session(engine) as session:
            yield session
    except Exception as e:
        logger.error(f"Error during database session: {e}")
        raise
