# Standard Library imports
import pytest

# Core Flask imports

# Third-party imports

# App imports
from app.db.firebase import Firebase
from app.services.firestore_service import USERS_COLLECTION, QUERIES_COLLECTION


@pytest.fixture(scope="module")
def request_config():
    """Fixure to provide requests configuration"""
    uid = "firebase_test_user"
    base_url = f"/{USERS_COLLECTION}/{uid}/{QUERIES_COLLECTION}"
    headers = {"Authorization": "Bearer fake-token", "Content-Type": "application/json"}

    return uid, base_url, headers


@pytest.fixture(scope="module")
def sample_data():
    """Fixture to provide sample query data."""
    return {
        "name": "test_query",
        "text": "SELECT * FROM drugs WHERE side_effects > 10",
    }


# Define the mock verification function
def mock_verify_token():
    """Return a mock token instead of verifying a real token."""
    return "mock_token"


@pytest.fixture(autouse=True)
def mock_auth(client, monkeypatch, request_config):
    """
    Automatically mock Firebase authentication for all tests.
    - Sets a mock user in the session.
    - Mocks `verify_token()` to always return a mock token.
    """
    # Set user session before tests
    with client.session_transaction() as session:
        uid, _, _ = request_config
        session["user"] = {"uid": uid, "email": "test@example.com"}

    # Apply the monkeypatch to replace the actual `verify_token` function
    monkeypatch.setattr("app.services.auth_service.verify_token", mock_verify_token)


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

    yield query_id  # Provide query_id for tests

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
    response = client.post(url, headers=headers, json=sample_data)

    # assert
    assert response.status_code == 201, f"Unexpected status: {response.status_code}"
    data = response.get_json()
    assert "query_id" in data, "Query ID missing in response"


def test_query_is_stored_correctly(client, request_config, sample_data):
    """Test that the query is correctly stored in Firestore."""

    # arrange
    db = Firebase.get_firestore()
    uid, url, headers = request_config

    # act - call API test to create a query
    response = client.post(url, headers=headers, json=sample_data)
    data = response.get_json()
    query_id = data["query_id"]

    # assert
    doc_ref = (
        db.collection(USERS_COLLECTION)
        .document(uid)
        .collection(QUERIES_COLLECTION)
        .document(query_id)
    )
    doc = doc_ref.get()

    # Ensure document exists
    assert doc.exists, f"Query {query_id} not found in Firestore"

    # Validate stored data
    stored_data = doc.to_dict()
    assert stored_data["name"] == sample_data["name"], "Query name mismatch"
    assert stored_data["text"] == sample_data["text"], "Query text mismatch"
    assert "created_at" in stored_data, "Missing 'created_at' timestamp"


@pytest.mark.parametrize(
    "method, endpoint, requires_body",
    [
        ("POST", "/users/other_user/queries", True),  # Requires a body
        # ("GET", "/users/other_user/data", False),  # No body needed
        # ("PUT", "/users/other_user/data", True),  # Requires a body
        # ("DELETE", "/users/other_user/data", False),  # No body needed
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

    assert response.status_code == 403  # Forbidden
