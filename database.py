"""Small SQLite/PostgreSQL bridge; all caller SQL is static and parameterized."""
import os
import sqlite3
from contextlib import contextmanager


class Database:
    def __init__(self, connection, postgres=False):
        self.connection = connection
        self.postgres = postgres

    def execute(self, sql, params=()):
        # Only our own static SQL uses question-mark placeholders.
        if self.postgres:
            sql = sql.replace("?", "%s")
        return self.connection.execute(sql, params)

    def insert_contact(self, name, favorite, notes):
        sql = "INSERT INTO contacts (name, favorite, notes) VALUES (?, ?, ?)"
        if self.postgres:
            return self.execute(sql + " RETURNING id", (name, favorite, notes)).fetchone()["id"]
        return self.execute(sql, (name, favorite, notes)).lastrowid


@contextmanager
def connect(db_path, database_url=""):
    if database_url:
        import psycopg
        from psycopg.rows import dict_row
        connection = psycopg.connect(database_url, row_factory=dict_row, connect_timeout=10)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        connection = sqlite3.connect(db_path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield Database(connection, bool(database_url))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize(db):
    primary_key = "BIGSERIAL PRIMARY KEY" if db.postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    timestamp = "CURRENT_TIMESTAMP::text" if db.postgres else "(datetime('now'))"
    foreign_key = "BIGINT" if db.postgres else "INTEGER"
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS contacts (
            id {primary_key}, name TEXT NOT NULL,
            favorite INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT {timestamp}
        )
    """)
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS contact_details (
            id {primary_key}, contact_id {foreign_key} NOT NULL
                REFERENCES contacts(id) ON DELETE CASCADE,
            type TEXT NOT NULL CHECK (type IN ('phone','email','social','address')),
            value TEXT NOT NULL
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_details_contact ON contact_details(contact_id)")
