import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# In production this would come from an environment variable, never hardcoded.
# We'll formalize .env usage properly once we containerize everything in Phase 15.

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:devpassword@localhost:5432/enterprise_rag")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class every ORM model inherits from --
# SQLAlchemy uses it to track all defined tables.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency: provides a database session per-request,
    and guarantees it's closed afterward even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
