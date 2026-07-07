"""SQLAlchemy engine and session. SQLite locally; set DATABASE_URL for PostgreSQL (e.g. Render)."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config import get_database_url

DATABASE_URL = get_database_url()

# SQLite needs check_same_thread for FastAPI sync routes
_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    Path("data").mkdir(exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables (use Alembic in production for migrations)."""
    import models.db_models  # noqa: F401 — register models

    Base.metadata.create_all(bind=engine)
