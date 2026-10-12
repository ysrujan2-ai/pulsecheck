import httpx
import os
import tempfile

from fastapi.testclient import TestClient
from main import app
import pytest


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


def test_monitored_sites_database():
    from database import (
        init_db,
        add_monitored_site,
        get_monitored_sites,
        remove_monitored_site,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = os.path.join(temp_dir, "monitored.db")
        init_db(db_name=test_db)

        site_id = add_monitored_site(
            "https://example.com",
            interval_minutes=5,
            db_name=test_db,
        )

        sites = get_monitored_sites(db_name=test_db)

        assert len(sites) == 1
        assert sites[0]["id"] == site_id
        assert sites[0]["url"] == "https://example.com"
        assert sites[0]["interval_minutes"] == 5
        assert sites[0]["is_enabled"] == 1

        removed = remove_monitored_site(
            site_id,
            db_name=test_db,
        )

        assert removed is True
        assert get_monitored_sites(db_name=test_db) == []



def test_update_monitored_site_last_checked():
    from database import (
        init_db,
        add_monitored_site,
        get_monitored_sites,
        update_monitored_site_last_checked,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = os.path.join(temp_dir, "monitored_timestamp.db")
        init_db(db_name=test_db)

        site_id = add_monitored_site(
            "https://example.com",
            interval_minutes=5,
            db_name=test_db,
        )

        updated = update_monitored_site_last_checked(
            site_id,
            db_name=test_db,
        )

        sites = get_monitored_sites(db_name=test_db)

        assert updated is True
        assert len(sites) == 1
        assert sites[0]["last_checked_at"] is not None


@pytest.mark.anyio
async def test_monitoring_cycle_skips_recently_checked_site(monkeypatch):
    from datetime import datetime, timezone
    import main

    site = {
        "id": 1,
        "url": "https://example.com",
        "interval_minutes": 5,
        "is_enabled": 1,
        "last_checked_at": datetime.now(timezone.utc).isoformat(),
    }

    monkeypatch.setattr(main, "get_monitored_sites", lambda: [site])

    async def unexpected_check(url):
        raise AssertionError("A recently checked site should be skipped")

    monkeypatch.setattr(main, "check_website", unexpected_check)

    await main.run_monitoring_cycle()



@pytest.mark.anyio
async def test_monitoring_cycle_skips_disabled_site(monkeypatch):
    import main

    site = {
        "id": 1,
        "url": "https://example.com",
        "interval_minutes": 5,
        "is_enabled": 0,
        "last_checked_at": None,
    }

    monkeypatch.setattr(main, "get_monitored_sites", lambda: [site])

    async def unexpected_check(url):
        raise AssertionError("A disabled site should not be checked")

    monkeypatch.setattr(main, "check_website", unexpected_check)

    await main.run_monitoring_cycle()


@pytest.mark.anyio
async def test_monitoring_cycle_checks_overdue_site(monkeypatch):
    from datetime import datetime, timedelta, timezone
    import main

    site = {
        "id": 1,
        "url": "https://example.com",
        "interval_minutes": 5,
        "is_enabled": 1,
        "last_checked_at": (
            datetime.now(timezone.utc) - timedelta(minutes=10)
        ).isoformat(),
    }

    checked_urls = []
    updated_ids = []

    monkeypatch.setattr(main, "get_monitored_sites", lambda: [site])

    async def fake_check_website(url):
        checked_urls.append(url)
        return {"is_up": True}

    monkeypatch.setattr(main, "check_website", fake_check_website)
    monkeypatch.setattr(
        main,
        "update_monitored_site_last_checked",
        lambda site_id: updated_ids.append(site_id),
    )

    await main.run_monitoring_cycle()

    assert checked_urls == ["https://example.com"]
    assert updated_ids == [1]



def test_scheduler_starts_and_stops():
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as client:
        assert app.state.scheduler.running is True

        job = app.state.scheduler.get_job("pulsecheck_monitoring")
        assert job is not None
        assert job.trigger.interval.total_seconds() == 60

    assert app.state.scheduler.running is False


def test_check_connection_error():
    from unittest.mock import AsyncMock, patch
    from fastapi.testclient import TestClient
    import httpx
    from main import app

    with patch(
        "main.httpx.AsyncClient",
        return_value=AsyncMock(
            __aenter__=AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            ),
            __aexit__=AsyncMock(return_value=False),
        ),
    ):
        with TestClient(app) as client:
            response = client.get(
                "/check",
                params={"url": "https://example.com"},
            )

    assert response.status_code == 502
