import time
import httpx
from fastapi import HTTPException
from pydantic import HttpUrl
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db, save_check, get_history
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="PulseCheck API",
    description="A simple API health monitoring service",
    version="1.0.0",
    lifespan=lifespan,
)

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



@app.get("/check")
async def check_website(url: HttpUrl):
    target_url = str(url)
    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(
            timeout=5.0,
            follow_redirects=True,
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

