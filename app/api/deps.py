from typing import Generator
from app.db.session import SessionLocal


def get_db() -> Generator:
    """
    Dependency function that provides a database session.
    Yields a database session and ensures it's properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()