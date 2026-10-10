# PulseCheck — Website Health Monitoring

**A lightweight website monitoring dashboard built with FastAPI, Python, and SQLite.**

PulseCheck allows users to check website availability, view HTTP status codes, measure response times, and review recent check history through a web-based dashboard.

## 🚀 Live Demo

**[Open PulseCheck](https://pulsecheck-xshk.onrender.com/)**

> Note: The free hosting instance may take a little time to respond after a period of inactivity.

## ✨ Features

- **Website health checks** — Check whether a website responds successfully.
- **HTTP status codes** — View the status code returned by a website.
- **Response time measurement** — Measure request duration in milliseconds.
- **Interactive dashboard** — Visualize response-time performance.
- **Recent check history** — View previously recorded website checks.
- **Error handling** — Handle invalid URLs, timeouts, and connection errors.
- **Persistent local storage** — Store check records in a SQLite database.
- **Automated tests** — Test API endpoints and database persistence using pytest.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| FastAPI | REST API and web server |
| HTTPX | Asynchronous HTTP requests |
| SQLite | Local database |
| HTML, CSS, JavaScript | Dashboard interface |
| Pytest | Automated testing |
| Uvicorn | ASGI server |
| Git and GitHub | Version control |
| Render | Deployment and hosting |

## 📸 Screenshots

Add screenshots of your live dashboard and response-time chart here.

## ⚙️ Run Locally

### 1. Clone the repository

bash
git clone https://github.com/ysrujan2-ai/pulsecheck.git
cd pulsecheck


### 2. Create and activate a virtual environment

**Windows PowerShell**

powershell
python -m venv .venv
.venv\Scripts\Activate.ps1


### 3. Install dependencies

bash
python -m pip install -r requirements.txt


### 4. Start the application

bash
python -m uvicorn main:app --reload


Open http://127.0.0.1:8000 in your browser.

## 🧪 Run Tests

bash
python -m pytest -v


The project currently has nine passing automated tests covering application endpoints, website-check scenarios, and database persistence.

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Dashboard homepage |
| GET | `/health` | Application health status |
| GET | `/check?url=https://example.com` | Check a website |
| GET | `/history` | Retrieve recent check history |

Interactive API documentation is available at `/docs` when the application is running.

## 📁 Project Structure

text
pulsecheck/
├── main.py
├── database.py
├── requirements.txt
├── test_main.py
├── README.md
└── static/
    ├── index.html
    ├── style.css
    └── script.js


## 🔮 Future Improvements

- Scheduled website monitoring
- Uptime percentage and availability statistics
- Persistent hosted database
- Alerts when a website becomes unavailable
- Monitoring multiple websites from one dashboard

## 👨‍💻 Author

Developed as a portfolio project to explore backend development, API design, asynchronous HTTP requests, database integration, automated testing, and cloud deployment.