# Standard Library imports

# Core Flask imports

# Third-party imports
import pytest
from firebase_admin import get_app, delete_app

# App imports
from app import create_app


@pytest.fixture(scope="module")
def app():
    app = create_app(config_name="test")
    yield app

    # Teardown: Clean up Firebase after the tests are done
    firebase_app = get_app()
    delete_app(firebase_app)


@pytest.fixture()
def client(app):
    return app.test_client()
