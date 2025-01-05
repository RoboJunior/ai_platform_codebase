from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.session import get_db

# Dependency to get the database session
def get_database_session(db: Session = Depends(get_db)):
    return db
