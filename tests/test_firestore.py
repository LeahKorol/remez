# Standard Library imports
import pytest

# Core Flask imports
from flask import g

# Third-party imports

# App imports
from app.db.firebase import Firebase
from app.services.firestore_service import USERS_COLLECTION, QUERIES_COLLECTION


@pytest.fixture
def client(app):
    """
    Provides a test client for making requests within an application context.
    This fixture ensures that tests run inside a valid Flask application context,
    allowing access to `g` (global request object) and `current_app`.
    """
    with app.test_client() as test_client:
        with app.app_context():
            yield test_client


@pytest.fixture(scope="module")
def request_config():
    """Fixure to provide requests configuration"""
    uid = "firebase_test_user"
    base_url = f"/{USERS_COLLECTION}/{uid}/{QUERIES_COLLECTION}"
    headers = {"Idtoken": "Bearer fake-token", "Content-Type": "application/json"}

    return uid, base_url, headers


@pytest.fixture(scope="module")
def sample_data():
    """Fixture to provide sample query data."""
    return {
        "name": "test_query",
        "text": "SELECT * FROM drugs WHERE side_effects > 10",
    }


# Define the mock verification function
def mock_verify_session_cookie(session_cookie, check_revoked):
    """Return a mock user instead of verifying the token."""
    return {"uid": "firebase_test_user", "email": "test@example.com"}


@pytest.fixture(autouse=True)
def mock_auth(client, monkeypatch, request_config):
    """
    Automatically mock Firebase authentication for all tests.
    - Sets a mock user in the session.
    - Mocks `verify_verify_session_cookie()` to always return a mock token.
    """
    # Set user session and g (request context) before tests
    with client.session_transaction() as session:
        session["session"] = "Bearer fake token"

    g.current_user = {"uid": "firebase_test_user", "email": "test@example.com"}

    # Apply the monkeypatch to replace the actual `verify_token` function
    monkeypatch.setattr(
        "firebase_admin.auth.verify_session_cookie", mock_verify_session_cookie
    )


@pytest.fixture(scope="module", autouse=True)
def firestore_test_data(app, sample_data, request_config):
    """Fixture to set up and tear down test data in Firestore."""

    db = Firebase.get_firestore()
    uid, _, _ = request_config
    query_id = "test_query_id"

    # Insert test query
    test_query = {
        **sample_data,
        "created_at": "2025-02-23T12:00:00Z",
    }
    db.collection(USERS_COLLECTION).document(uid).collection(
        QUERIES_COLLECTION
    ).document(query_id).set(test_query)

    yield query_id, test_query  # Provides a query for tests

    # Cleanup test data after tests
    docs = (
        db.collection(USERS_COLLECTION)
        .document(uid)
        .collection(QUERIES_COLLECTION)
        .list_documents(page_size=20)
    )
    for doc in docs:
        doc.delete()
    db.collection("users").document(uid).delete()


def test_create_query(client, sample_data, request_config):
    """Test creating a query via POST request."""
    # arrange
    _, url, headers = request_config

    # act
    g.current_user = {"uid": "firebase_test_user", "email": "test@example.com"}
    response = client.post(url, headers=headers, json=sample_data)

    # assert
    assert response.status_code == 201, f"Unexpected status: {response.status_code}"
    data = response.get_json()
    assert "id" in data, "Query ID missing in response"
    assert "created_at" in data, "Query creation time missing in response"


def test_query_is_stored_correctly(client, request_config, sample_data):
    """Test that the query is correctly stored in Firestore."""
    # arrange
    db = Firebase.get_firestore()
    uid, url, headers = request_config

    # act - call API test to create a query
    response = client.post(url, headers=headers, json=sample_data)
    data = response.get_json()
    query_id = data["id"]

    # assert
    doc_ref = (
        db.collection(USERS_COLLECTION)
        .document(uid)
        .collection(QUERIES_COLLECTION)
        .document(query_id)
    )
    doc = doc_ref.get()

    # Ensure document exists
    assert doc is not None, f"Failed to retrieve document {query_id}"
    assert doc.exists, f"Query {query_id} not found in Firestore"

    # Validate stored data
    stored_data = doc.to_dict()
    assert stored_data["name"] == sample_data["name"], "Query name mismatch"
    assert stored_data["text"] == sample_data["text"], "Query text mismatch"
    assert "created_at" in stored_data, "Missing 'created_at' timestamp"


def test_get_user_query(client, request_config, firestore_test_data):
    """Test getting user's query via GET request"""
    # arrange
    _, url, headers = request_config
    query_id, query_data = firestore_test_data

    # act
    response = client.get(f"{url}/{query_id}", headers=headers)
    data = response.get_json()

    # assert
    assert response.status_code == 200, f"Unexpected status: {response.status_code}"
    assert data["id"] == query_id, "Query id mismatch"
    assert data["name"] == query_data["name"], "Query name mismatch"


def test_get_user_queries(client, request_config, firestore_test_data):
    """Test getting user's queries via GET request"""
    # arrange
    _, url, headers = request_config
    query_id, _ = firestore_test_data

    # act
    response = client.get(url, headers=headers)
    stored_queries = response.get_json()

    # assert
    assert response.status_code == 200, f"Unexpected status: {response.status_code}"
    assert any(
        query["id"] == query_id for query in stored_queries
    ), f"Query {query_id} not found"


def test_update_user_query(client, request_config, firestore_test_data):
    """Test update user's query via a PATCH request"""
    # arrange
    _, url, headers = request_config
    query_id, query_data = firestore_test_data
    update_data = {"name": "updated_test_query"}

    # act
    response = client.patch(f"{url}/{query_id}", headers=headers, json=update_data)
    data = response.get_json()

    # assert
    assert response.status_code == 200, f"Unexpected status: {response.status_code}"
    assert data["id"] == query_id, "The wrong query was changed"
    assert data["name"] == update_data["name"], "The fields wasn't updated"
    assert data["text"] == query_data["text"], "The wrong field was changed"


def test_delete_user_query(client, request_config, firestore_test_data):
    """Test deleting a user's query via DELETE request"""
    # arrange
    _, url, headers = request_config
    query_id, _ = firestore_test_data

    # act
    response = client.delete(f"{url}/{query_id}", headers=headers)

    # assert
    assert response.status_code == 204, f"Unexpected status: {response.status_code}"


def test_query_was_deleted(firestore_test_data, request_config):
    """Test that a deleted query no longer exists in Firestore"""
    query_id, _ = firestore_test_data
    uid, _, _ = request_config
    db = Firebase.get_firestore()

    doc_ref = (
        db.collection(USERS_COLLECTION)
        .document(uid)
        .collection(QUERIES_COLLECTION)
        .document(query_id)
    )
    doc = doc_ref.get()

    # Ensure document retrieval was successful
    assert doc is not None, f"Failed to retrieve document {query_id}"
    assert not doc.exists, f"Query {query_id} exists in Firestore"


@pytest.mark.parametrize(
    "method, endpoint, requires_body",
    [
        ("POST", "/users/other_user/queries", True),  # Requires a body
        ("GET", "/users/other_user/queries/query_id", False),  # No body needed
        ("GET", "/users/other_user/queries", False),  # No body needed
        ("PATCH", "/users/other_user/queries/query_id", True),  # Requires a body
        ("DELETE", "/users/other_user/queries/query_id", False),  # No body needed
    ],
)
def test_user_cannot_access_other_users_data(
    client, method, endpoint, requires_body, sample_data, request_config
):
    request_method = getattr(client, method.lower())  # Dynamically get request method
    _, _, headers = request_config

    if requires_body:
        response = request_method(endpoint, headers=headers, json=sample_data)
    else:
        response = request_method(endpoint, headers=headers)

    # Forbidden
    assert response.status_code == 403, f"Unexpected status: {response.status_code}"
