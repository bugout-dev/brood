"""
Connections to external services
"""
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm.session import Session, sessionmaker

from .settings import (
    BROOD_DB_URI,
    BROOD_DB_URI_READ_ONLY,
    BROOD_POOL_SIZE,
    BROOD_DB_STATEMENT_TIMEOUT_MILLIS,
    BROOD_DB_POOL_RECYCLE_SECONDS,
)


def create_brood_engine(
    url: Optional[str],
    pool_size: int,
    statement_timeout: int,
    pool_recycle: int = BROOD_DB_POOL_RECYCLE_SECONDS,
):
    # Pooling: https://docs.sqlalchemy.org/en/14/core/pooling.html#sqlalchemy.pool.QueuePool
    # Statement timeout: https://stackoverflow.com/a/44936982
    return create_engine(
        url=url,
        pool_size=pool_size,
        pool_recycle=pool_recycle,
        connect_args={"options": f"-c statement_timeout={statement_timeout}"},
    )


engine = create_brood_engine(
    url=BROOD_DB_URI,
    pool_size=BROOD_POOL_SIZE,
    statement_timeout=BROOD_DB_STATEMENT_TIMEOUT_MILLIS,
    pool_recycle=BROOD_DB_POOL_RECYCLE_SECONDS,
)
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


# Read only
RO_engine = create_brood_engine(
    url=BROOD_DB_URI_READ_ONLY,
    pool_size=BROOD_POOL_SIZE,
    statement_timeout=BROOD_DB_STATEMENT_TIMEOUT_MILLIS,
    pool_recycle=BROOD_DB_POOL_RECYCLE_SECONDS,
)
RO_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=RO_engine)


def yield_db_read_only_session() -> Session:
    """
    Yields read only database connection (created using environment variables).
    As per FastAPI docs:
    https://fastapi.tiangolo.com/tutorial/sql-databases/#create-a-dependency
    """
    session = RO_SessionLocal()
    try:
        yield session
    finally:
        session.close()
