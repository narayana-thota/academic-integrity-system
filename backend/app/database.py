import os
from pathlib import Path
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

# Load the project root .env file
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3307")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# Automatically map the existing MySQL tables.
Base = automap_base()


def reflect_database():
    Base.prepare(autoload_with=engine)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
