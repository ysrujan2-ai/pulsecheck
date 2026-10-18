# PulseCheck — Website Health Monitoring

PulseCheck is a website health monitoring API and dashboard built with **FastAPI**, **Python**, and a database layer that supports **Neon PostgreSQL** or local **SQLite**. It checks website availability, records HTTP status and response time, stores check history, and supports scheduled monitoring for registered sites.

**Live demo:** [https://pulsecheck-xshk.onrender.com](https://pulsecheck-xshk.onrender.com)

> **Hosting note:** The demo uses Render's free web service, which can spin down after inactivity. Requests may take longer while the service wakes up, and its in-process scheduler is not guaranteed to run continuously while the service is asleep.

## Features

- **Website health checks** — Check public HTTP/HTTPS URLs and follow the response status.
- **Response-time measurement** — Record request duration in milliseconds.
- **Check history** — Store and retrieve previous checks.
- **Scheduled monitoring** — Register websites with configurable intervals (5–1,440 minutes).
- **Monitoring management API** — Create, list, and remove monitored websites.
- **Database support** — Use Neon PostgreSQL through `DATABASE_URL`, or SQLite for local development when no database URL is configured.
- **Error handling** — Handle invalid URLs, timeouts, and connection failures.
- **Dashboard** — View website checks and response-time information in a browser.
- **Automated tests** — Test API behavior and database persistence with pytest.

## Tech stack

| Technology | Purpose |
|---|---|
| Python | Application language |
| FastAPI | API framework |
| HTTPX | Asynchronous HTTP requests |
| Neon PostgreSQL / SQLite | Persistent database options |
| psycopg | PostgreSQL driver |
| HTML, CSS, JavaScript | Web dashboard |
| APScheduler | In-process scheduled monitoring |
| pytest | Automated tests |
| Uvicorn | ASGI server |
| GitHub | Version control and collaboration |
| Render | Application hosting |

## Architecture overview

1. The dashboard or a client sends a request to the FastAPI application.
2. The API validates the URL and checks the target website using HTTPX.
3. The result (status code, availability, response time, timestamp, and URL) is saved through the database layer.
4. The history endpoint returns stored results to the dashboard or API client.
5. Registered sites are checked by the in-process scheduler when their configured interval is due.

## Run locally

### Requirements

- Python 3.11 or newer
- Git

### 1. Clone the repository

```bash
git clone https://github.com/ysrujan2-ai/pulsecheck.git
cd pulsecheck
```

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the database (optional)

For local SQLite development, leave `DATABASE_URL` unset. The application uses SQLite by default.

To use Neon PostgreSQL, create a `.env` file in the project root and add your own Neon connection URI:

```dotenv
DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST/neondb?sslmode=require
```

Replace the example with the complete connection URI from Neon. Keep `.env` private and **never commit real credentials to GitHub**. Configure the same variable in your hosting provider's environment settings for deployment.

### 5. Start the application

```bash
python -m uvicorn main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the dashboard. Interactive API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the dashboard homepage |
| `GET` | `/health` | Reports application health |
| `GET` | `/check?url=https://example.com` | Checks a website and records the result |
| `GET` | `/history` | Returns recent check history |
| `POST` | `/monitored-sites` | Registers a website for scheduled monitoring |
| `GET` | `/monitored-sites` | Lists registered monitored websites |
| `DELETE` | `/monitored-sites/{site_id}` | Removes a monitored website |

### Register a monitored website

Send a `POST` request to `/monitored-sites` with JSON such as:

```json
{
  "url": "https://www.iana.org/",
  "interval_minutes": 5
}
```

The supported interval is 5 to 1,440 minutes. The scheduler runs inside the web application; on a host that sleeps or restarts, scheduled checks may be delayed. For continuous production monitoring, use an always-on worker or an external scheduler.

## Run tests

Run the application test suite with:

```bash
python -m pytest test_main.py -v
```

## Project structure

```text
pulsecheck/
├── main.py              # FastAPI routes and monitoring scheduler
├── database.py          # SQLite/PostgreSQL persistence
├── requirements.txt     # Python dependencies
├── test_main.py         # Application tests
├── README.md
├── screenshots/         # Dashboard screenshots
└── static/
    ├── index.html
    ├── style.css
    └── script.js
```

## Screenshots

### Dashboard

![PulseCheck dashboard](screenshots/dashoborad1.png)

### Response-time performance

![Response-time performance](screenshots/rspns3.png)

### Recent check history

![Recent check history](screenshots/db2.png)

## Security and deployment notes

- Do not commit `.env`, passwords, or database connection strings.
- Keep `DATABASE_URL` configured as an environment variable in the deployment provider.
- The service is intended as a portfolio/demo project; free-tier hosting and an in-process scheduler do not provide an uptime guarantee.

## Author

Built as a portfolio project to practice backend development, REST API design, asynchronous HTTP requests, database integration, scheduled jobs, automated testing, and cloud deployment.
