from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings, Config

# Database URL (SQLite in this case)
DATABASE_URL = Config.DB_CONFIG.format(get_settings().DATABASE_NAME)

# Create an engine for the database connection
engine = create_engine(DATABASE_URL, echo=True)

# Define a base class for ORM models
Base = declarative_base()

# Set up a session to interact with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """ Dependency to provide a session for DB interaction """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()