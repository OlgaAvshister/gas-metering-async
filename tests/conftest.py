"""Shared fixtures for integration tests.

A real PostgreSQL runs in a container for the whole test session: the behaviour
under test is the database's own — unique constraints, ON CONFLICT, transaction
boundaries — so a mock would test nothing. Each test gets a clean set of tables
rather than a fresh container, which keeps the suite fast.
"""

from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row
from testcontainers.postgres import PostgresContainer

MIGRATIONS = sorted((Path(__file__).parent.parent / "db" / "migrations").glob("*.sql"))
SEEDS = sorted((Path(__file__).parent.parent / "db" / "seeds").glob("*.sql"))


@pytest.fixture(scope="session")
def postgres_url():
    with PostgresContainer("postgres:16", driver=None) as container:
        url = container.get_connection_url()
        with psycopg.connect(url, autocommit=True) as conn:
            for path in MIGRATIONS:
                conn.execute(path.read_text(encoding="utf-8"))
        yield url


@pytest.fixture
def conn(postgres_url):
    with psycopg.connect(postgres_url, row_factory=dict_row) as connection:
        yield connection
        connection.rollback()


@pytest.fixture
def seeded(conn):
    """Reference data, rolled back after each test."""
    for path in SEEDS:
        conn.execute(path.read_text(encoding="utf-8"))
    return conn
