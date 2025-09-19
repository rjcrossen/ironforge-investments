"""
Database connection utility module for the Ironforge collection service.

This module provides functions to establish and manage database connections.
"""

import os
from collections.abc import Generator
from contextlib import contextmanager

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables
load_dotenv(find_dotenv())

# Database connection configuration
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "DB")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create sessionmaker factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base reference
Base = declarative_base()


def get_engine():
    """Get the SQLAlchemy engine instance.

    Returns:
        The SQLAlchemy engine instance.
    """
    return engine


def get_session() -> Session:
    """Create and get a new database session.

    Returns:
        A new SQLAlchemy session.
    """
    return SessionLocal()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for database session handling with automatic commit/rollback.

    Yields:
        Session: The database session.

    Example:
        with db_session() as session:
            results = session.query(MyModel).all()
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
