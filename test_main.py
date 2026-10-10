import httpx
import os
import tempfile

from fastapi.testclient import TestClient
from main import app


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_homepage():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_history():
    with TestClient(app) as client:
        response = client.get("/history")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


from unittest.mock import AsyncMock, patch
from httpx import Response


def test_check_website_success():
    mock_response = Response(
    200,
    request=httpx.Request("GET", "https://example.com"),
)

    with patch(
        "main.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        with TestClient(app) as client:
            response = client.get(
                "/check",
                params={"url": "https://example.com"},
            )

    assert response.status_code == 200
    assert response.json()["is_up"] is True
    assert response.json()["status_code"] == 200


def test_check_website_404():
    mock_response = Response(
        404,
        request=httpx.Request("GET", "https://example.com"),
    )

    with patch(
        "main.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        with TestClient(app) as client:
            response = client.get(
                "/check",
                params={"url": "https://example.com"},
            )

    assert response.status_code == 200
    assert response.json()["is_up"] is False
    assert response.json()["status_code"] == 404



def test_check_website_invalid_url():
    with TestClient(app) as client:
        response = client.get(
            "/check",
            params={"url": "not-a-valid-url"},
        )

    assert response.status_code == 422


def test_check_website_timeout():
    import httpx

    with patch(
        "main.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        side_effect=httpx.TimeoutException("Test timeout"),
    ):
        with TestClient(app) as client:
            response = client.get(
                "/check",
                params={"url": "https://example.com"},
            )

    assert response.status_code == 504
    assert response.json()["detail"] == "Website request timed out"


def test_check_website_connection_error():
    with patch(
        "main.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        side_effect=httpx.RequestError(
            "Connection failed",
            request=httpx.Request(
                "GET", "https://example.com"
            ),
        ),
    ):
        with TestClient(app) as client:
            response = client.get(
                "/check",
                params={"url": "https://example.com"},
            )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Could not connect to the website"
    )



def test_database_persistence():
    from database import init_db, save_check, get_history

    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = os.path.join(temp_dir, "test.db")

        init_db(db_name=test_db)

        save_check(
            "https://example.com",
            200,
            True,
            150.0,
            db_name=test_db,
        )

        history = get_history(db_name=test_db)

        assert len(history) == 1
        assert history[0]["url"] == "https://example.com"
        assert history[0]["status_code"] == 200
        assert history[0]["is_up"] == 1
