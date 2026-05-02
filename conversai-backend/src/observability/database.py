"""
Observability Database Module

This module handles SQLite database initialization, connection management,
and schema creation for the ConversAI observability system.

The database stores metadata and references to artifacts, NOT full base64 blobs.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional
from pathlib import Path

# Database file location (project root)
DB_PATH = Path(__file__).parent.parent.parent / "observability.db"

# Ensure database directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """
    Get a database connection with proper settings.
    
    Returns:
        SQLite connection with WAL mode and foreign keys enabled
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


@contextmanager
def get_transaction():
    """
    Context manager for safe database transactions.
    
    Automatically commits on success, rolls back on error.
    
    Usage:
        with get_transaction() as conn:
            conn.execute("INSERT INTO ...")
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database():
    """
    Initialize the database schema if it doesn't exist.
    
    Creates:
    - explanation_runs table
    - run_counter table (for human-readable sequential IDs)
    - Indexes for common queries
    
    This is called automatically on first import.
    """
    with get_transaction() as conn:
        # Create main table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS explanation_runs (
                run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('success', 'partial', 'failed')),
                total_time_ms REAL NOT NULL,
                payload_json TEXT NOT NULL
            )
        """)
        
        # Schema migration: Add new structured and timing columns if they don't exist
        new_columns = [
            ("explanation_time_ms", "REAL"),
            ("visual_time_ms", "REAL"),
            ("voice_time_ms", "REAL"),
            ("aggregation_time_ms", "REAL"),
            ("user_input_text", "TEXT"),
            ("narration_text", "TEXT"),
            ("segment_count", "INTEGER"),
            ("visual_count", "INTEGER")
        ]
        for col_name, col_type in new_columns:
            try:
                conn.execute(f"ALTER TABLE explanation_runs ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError as e:
                # Ignore duplicate column errors, meaning the column already exists
                if "duplicate column name" not in str(e).lower():
                    raise e
        
        
        # Create run counter table for human-readable sequential IDs
        # CHANGE 1: Human-Readable Run IDs
        # This table maintains a monotonically increasing counter
        # that persists across restarts and prevents race conditions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS run_counter (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_run INTEGER NOT NULL DEFAULT 0
            )
        """)
        
        # Initialize counter if it doesn't exist
        conn.execute("""
            INSERT OR IGNORE INTO run_counter (id, last_run) 
            VALUES (1, 0)
        """)
        
        # Create indexes for common queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON explanation_runs(created_at)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status 
            ON explanation_runs(status)
        """)
        
        # Add index for total_time_ms to improve performance queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_total_time_ms 
            ON explanation_runs(total_time_ms)
        """)


def generate_run_id() -> str:
    """
    Generate a human-readable, sequential run ID.
    
    CHANGE 1: Human-Readable Run IDs
    
    Generates IDs in the format: run_001, run_002, run_143, etc.
    
    Implementation:
    - Atomically increments counter in run_counter table
    - Zero-padded to at least 3 digits
    - Monotonically increasing
    - Persists across restarts
    - Thread-safe via SQLite transaction
    
    Returns:
        Sequential run ID (e.g., "run_001", "run_042", "run_143")
    """
    with get_transaction() as conn:
        # Atomically increment and retrieve the counter
        # This ensures no race conditions even with concurrent requests
        conn.execute("""
            UPDATE run_counter 
            SET last_run = last_run + 1 
            WHERE id = 1
        """)
        
        # Get the new counter value
        cursor = conn.execute("""
            SELECT last_run 
            FROM run_counter 
            WHERE id = 1
        """)
        
        counter = cursor.fetchone()[0]
        
        # Format as zero-padded run ID (minimum 3 digits)
        return f"run_{counter:03d}"


# Auto-initialize on module import
try:
    initialize_database()
except Exception as e:
    # Log warning but don't crash
    import warnings
    warnings.warn(f"Failed to initialize observability database: {e}")


__all__ = ["get_connection", "get_transaction", "DB_PATH", "initialize_database", "generate_run_id"]
