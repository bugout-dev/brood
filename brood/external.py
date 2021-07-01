"""
Connections to external services
"""
from sqlalchemy import create_engine
from sqlalchemy.orm.session import Session, sessionmaker

from .settings import DB_URI


if DB_URI is None:
    raise ValueError("BROOD_DB_URI environment variable not set")
engine = create_engine(DB_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def yield_db_session_from_env() -> Session:
    """
    Creates an active database session using configuration from the environment and yields it as
    per FastAPI docs:
    https://fastapi.tiangolo.com/tutorial/sql-databases/#create-a-dependency

    Behaves identically to db_session_from_env in all other respects.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
