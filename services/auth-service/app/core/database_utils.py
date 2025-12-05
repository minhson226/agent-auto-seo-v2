"""Database utilities for cross-database compatibility."""

import os

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB


def is_sqlite() -> bool:
    """Check if the current database is SQLite."""
    db_url = os.environ.get("DATABASE_URL", "")
    return "sqlite" in db_url


def get_table_args() -> dict:
    """Get table args with schema if not using SQLite.
    
    PostgreSQL uses 'autoseo' schema, SQLite doesn't support schemas.
    """
    if is_sqlite():
        return {}
    return {"schema": "autoseo"}


def get_json_type():
    """Get JSON type based on database.
    
    PostgreSQL uses JSONB for better indexing, SQLite uses JSON.
    """
    if is_sqlite():
        return JSON
    return JSONB


def get_foreign_key_reference(table: str, column: str = "id") -> str:
    """Get foreign key reference with schema qualification.
    
    Args:
        table: The table name
        column: The column name (default: 'id')
    
    Returns:
        Schema-qualified reference for PostgreSQL, simple reference for SQLite.
    """
    if is_sqlite():
        return f"{table}.{column}"
    return f"autoseo.{table}.{column}"
