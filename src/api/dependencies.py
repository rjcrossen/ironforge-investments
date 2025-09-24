"""
Database dependencies for FastAPI routes.
"""

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from repository.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session for FastAPI dependency injection.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()