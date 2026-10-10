
import os
import sqlite3
from contextlib import closing

DB_NAME = os.getenv("PULSECHECK_DB", "pulsecheck.db")


def init_db(db_name=DB_NAME):
    with closing(sqlite3.connect(db_name)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    status_code INTEGER,
                    is_up BOOLEAN NOT NULL,
                    response_time_ms REAL,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)


def save_check(
    url,
    status_code,
    is_up,
    response_time_ms,
    db_name=DB_NAME,
):
    with closing(sqlite3.connect(db_name)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO checks
                (url, status_code, is_up, response_time_ms)
                VALUES (?, ?, ?, ?)
                """,
                (url, status_code, is_up, response_time_ms),
            )


def get_history(limit=20, db_name=DB_NAME):
    with closing(sqlite3.connect(db_name)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM checks
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]
