# PulseCheck — Website Health Monitor

PulseCheck is a lightweight website monitoring application built with **FastAPI, Python, and SQLite**. It checks website availability, measures response time, handles connection failures, and stores monitoring results for later review.

## Features

- **Website health checks** — check whether a URL responds successfully.
- **Response time tracking** — measure how long a website takes to respond.
- **Error handling** — handle request timeouts and connection failures.
- **Monitoring history** — store and retrieve previous checks using SQLite.
- **Dashboard** — view monitoring results through a web interface.
- **Automated tests** — test API endpoints, URL validation, error handling, and database persistence.

## Tech Stack

- **Backend:** Python, FastAPI
- **HTTP requests:** HTTPX
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Testing:** Pytest, FastAPI TestClient




## Getting Started

### Prerequisites

- Python 3.10 or newer
- Git (optional, for cloning the repository)

### Installation

1. Clone the repository or download the project.
2. Open a terminal in the project directory.
3. Create and activate a virtual environment.

**Windows PowerShell:**

powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

4. Install the dependencies:

powershell
python -m pip install fastapi uvicorn httpx pytest


5. Start the application:

powershell
python -m uvicorn main:app --reload


6. Open `http://127.0.0.1:8000` in your browser.

### Running Tests

Run the automated test suite with:

powershell
python -m pytest -v

