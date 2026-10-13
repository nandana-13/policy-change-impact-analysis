from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = (
    "postgresql+psycopg2://postgres:postgres@localhost:5432/"
    "policy_impact_analysis"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """
    FastAPI database dependency.

    Creates one database session per request
    and closes it after the request finishes.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()