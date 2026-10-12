import time
import sqlite3
import httpx

from fastapi import FastAPI, HTTPException
from pydantic import HttpUrl, Field, BaseModel
from contextlib import asynccontextmanager
from database import (
    init_db,
    save_check,
    get_history,
    add_monitored_site,
    get_monitored_sites,
    remove_monitored_site,
    update_monitored_site_last_checked,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime, timezone
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import ipaddress
import socket
from urllib.parse import urlsplit






@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_monitoring_cycle,
        trigger="interval",
        seconds=60,
        id="pulsecheck_monitoring",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=30,
    )

    scheduler.start()
    app.state.scheduler = scheduler

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="PulseCheck API",
    description="A simple API health monitoring service",
    version="1.0.0",
    lifespan=lifespan,
)


class MonitoredSiteCreate(BaseModel):
    url: HttpUrl
    interval_minutes: int = Field(default=5, ge=5, le=1440)




BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "PulseCheck API",
    }


def validate_public_url(url: str) -> None:
    """Reject URLs that target private or non-public network addresses."""
    parsed = urlsplit(url)

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400,
            detail="Only HTTP and HTTPS URLs are allowed",
        )

    if not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(
            status_code=400,
            detail="Invalid URL",
        )

    hostname = parsed.hostname.lower()

    if hostname == "localhost" or hostname.endswith(
        (".localhost", ".local", ".internal")
    ):
        raise HTTPException(
            status_code=400,
            detail="Private or internal destinations are not allowed",
        )

    try:
        addresses = {
            result[4][0]
            for result in socket.getaddrinfo(
                hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        }

        if not addresses:
            raise HTTPException(
                status_code=400,
                detail="Could not resolve hostname",
            )

        for address in addresses:
            ip = ipaddress.ip_address(address)

            if not ip.is_global:
                raise HTTPException(
                    status_code=400,
                    detail="Private or internal destinations are not allowed",
                )

    except (socket.gaierror, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Invalid or unresolvable hostname",
        )


@app.get("/check")
async def check_website(url: HttpUrl):
    
    target_url = str(url)
    validate_public_url(target_url)
    start_time = time.perf_counter()


    try:
        async with httpx.AsyncClient(
            timeout=5.0,
            follow_redirects=False,
        ) as client:
            response = await client.get(target_url)

        elapsed_ms = round(
            (time.perf_counter() - start_time) * 1000, 2
        )
        is_up = response.is_success

        save_check(
            target_url,
            response.status_code,
            is_up,
            elapsed_ms,
        )

        return {
            "url": target_url,
            "status_code": response.status_code,
            "is_up": is_up,
            "response_time_ms": elapsed_ms,
        }

    except httpx.TimeoutException:
        elapsed_ms = round(
            (time.perf_counter() - start_time) * 1000, 2
        )

        save_check(
            target_url,
            None,
            False,
            elapsed_ms,
        )

        raise HTTPException(
            status_code=504,
            detail="Website request timed out",
        )

    except httpx.RequestError as exc:
        elapsed_ms = round(
            (time.perf_counter() - start_time) * 1000, 2
        )

        save_check(
            target_url,
            None,
            False,
            elapsed_ms,
        )

        print(f"Connection error for {target_url}: {exc!r}")

        raise HTTPException(
            status_code=502,
            detail="Could not connect to the website",
        )


@app.get("/history")
def check_history():
    return get_history()


@app.post("/monitored-sites", status_code=201)
def create_monitored_site(site: MonitoredSiteCreate):
    target_url = str(site.url)

    try:
        site_id = add_monitored_site(
            target_url,
            interval_minutes=site.interval_minutes,
        )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="This website is already registered",
        )

    return {
        "id": site_id,
        "url": target_url,
        "interval_minutes": site.interval_minutes,
        "is_enabled": True,
    }


@app.get("/monitored-sites")
def list_monitored_sites():
    return get_monitored_sites()


@app.delete("/monitored-sites/{site_id}")
def delete_monitored_site(site_id: int):
    removed = remove_monitored_site(site_id)

    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Monitored website not found",
        )

    return {"message": "Monitored website removed"}



async def run_monitoring_cycle():
    """Check enabled websites when their monitoring interval is due."""
    sites = get_monitored_sites()
    now = datetime.now(timezone.utc)

    for site in sites:
        if not site["is_enabled"]:
            continue

        last_checked = site["last_checked_at"]

        if last_checked:
            try:
                last_checked_at = datetime.fromisoformat(
                    last_checked.replace("Z", "+00:00")
                )

                if last_checked_at.tzinfo is None:
                    last_checked_at = last_checked_at.replace(
                        tzinfo=timezone.utc
                    )

                elapsed_seconds = (
                    now - last_checked_at
                ).total_seconds()

                interval_seconds = site["interval_minutes"] * 60

                if elapsed_seconds < interval_seconds:
                    continue

            except (ValueError, TypeError):
                # Check the site if its timestamp is invalid.
                pass

        try:
            await check_website(url=site["url"])
        except HTTPException as exc:
            print(
                f"Monitoring failed for {site['url']}: "
                f"{exc.status_code} - {exc.detail}"
            )
        finally:
            update_monitored_site_last_checked(site["id"])
