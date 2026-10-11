
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

            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitored_sites (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     url TEXT NOT NULL UNIQUE,
                     interval_minutes INTEGER NOT NULL DEFAULT 5,
                     is_enabled BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checked_at TIMESTAMP
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


def add_monitored_site(
    url,
    interval_minutes=5,
    db_name=DB_NAME,
):
    with closing(sqlite3.connect(db_name)) as conn:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO monitored_sites (url, interval_minutes)
                VALUES (?, ?)
                """,
                (url, interval_minutes),
            )
            site_id = cursor.lastrowid

        return site_id


def get_monitored_sites(db_name=DB_NAME):
    with closing(sqlite3.connect(db_name)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM monitored_sites
            ORDER BY id DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]


def remove_monitored_site(site_id, db_name=DB_NAME):
    with closing(sqlite3.connect(db_name)) as conn:
        with conn:
            cursor = conn.execute(
                "DELETE FROM monitored_sites WHERE id = ?",
                (site_id,),
            )
            return cursor.rowcount > 0


    
def add_monitored_site(
    url,
    interval_minutes=5,
    db_name=DB_NAME,
):
    with closing(sqlite3.connect(db_name)) as conn:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO monitored_sites (url, interval_minutes)
                VALUES (?, ?)
                """,
                (url, interval_minutes),
            )
            site_id = cursor.lastrowid

        return site_id


def get_monitored_sites(db_name=DB_NAME):
    with closing(sqlite3.connect(db_name)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM monitored_sites
            ORDER BY id DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]


def remove_monitored_site(site_id, db_name=DB_NAME):
    with closing(sqlite3.connect(db_name)) as conn:
        with conn:
            cursor = conn.execute(
                "DELETE FROM monitored_sites WHERE id = ?",
                (site_id,),
            )
            return cursor.rowcount > 0


def update_monitored_site_last_checked(site_id, db_name=DB_NAME):
    with closing(sqlite3.connect(db_name)) as conn:
        with conn:
            cursor = conn.execute(
                """
                UPDATE monitored_sites
                SET last_checked_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (site_id,),
            )
            return cursor.rowcount > 0

