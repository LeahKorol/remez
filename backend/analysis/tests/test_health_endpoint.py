from rest_framework.test import APIClient


def test_health_endpoint_returns_ok(mocker):
    client = APIClient()
    cursor = mocker.MagicMock()
    cursor.fetchone.return_value = (1,)
    context_manager = mocker.MagicMock()
    context_manager.__enter__.return_value = cursor
    context_manager.__exit__.return_value = False
    mocker.patch("backend.health.connection.cursor", return_value=context_manager)

    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_endpoint_returns_503_when_db_unavailable(mocker):
    client = APIClient()
    mocker.patch("backend.health.connection.cursor", side_effect=Exception("db down"))

    response = client.get("/api/v1/health/")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "db": "error"}
