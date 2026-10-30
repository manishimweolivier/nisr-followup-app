"""
Database Connection and Transaction Management for FollowUp
Persistent local SQLite storage with WAL mode and foreign key constraints.
"""

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Any, List, Dict, Optional
import pandas as pd
import config

def get_db_path() -> Path:
    """Return the absolute path to the SQLite database file."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return config.DB_PATH

def get_raw_connection() -> sqlite3.Connection:
    """
    Create and return a raw SQLite connection with row factory
    and required PRAGMA optimizations.
    """
    db_file = get_db_path()
    conn = sqlite3.connect(
        str(db_file),
        check_same_thread=False,
        timeout=30.0
    )
    conn.row_factory = sqlite3.Row
    # Enable foreign keys and write-ahead logging for safety & concurrency
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections ensuring auto-commit
    on success and rollback on exception.
    """
    conn = get_raw_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute_query(sql: str, params: tuple = ()) -> List[sqlite3.Row]:
    """Execute a SELECT query and return all rows."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

def execute_single(sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    """Execute a query and return a single row or None."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()

def execute_statement(sql: str, params: tuple = ()) -> int:
    """
    Execute an INSERT, UPDATE, or DELETE statement.
    Returns the lastrowid for INSERT or rowcount for UPDATE/DELETE.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

def query_to_dataframe(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a SELECT query and return the result as a Pandas DataFrame."""
    with get_db_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)
