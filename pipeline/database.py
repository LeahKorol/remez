from typing import Annotated

from core.config import get_settings
from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

settings = get_settings()


engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a new database session for dependency injection in API endpoints"""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def create_session():
    """Create a new database session for non-API usage"""
    return Session(engine)
