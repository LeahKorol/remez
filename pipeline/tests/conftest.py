"""
Shared pytest fixtures for pipeline tests
"""

import pytest
from api.v1.routes.pipeline import router
from fastapi import FastAPI
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


@pytest.fixture(scope="session")
def test_engine():
    """Create a single test database engine for the entire test session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    yield engine  # each test gets this engine

    engine.dispose()  # Cleanup: Dispose engine after all tests


@pytest.fixture
def test_session(test_engine):
    """Create a fresh test database session for each test with automatic cleanup."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    # Cleanup: Rollback transaction and close connection after each test
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_app(test_session):
    """Create test FastAPI app with dependency override"""
    app = FastAPI()
    app.include_router(router)

    # Override the database dependency
    def override_get_session():
        yield test_session

    from database import get_session

    app.dependency_overrides[get_session] = override_get_session
    return app
