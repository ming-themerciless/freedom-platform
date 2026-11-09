"""Compatibility with the current SQLAlchemy series, checked without a database.

SQLAlchemy 2.1 deprecated `select().distinct(expr)` as the spelling of PostgreSQL's
`DISTINCT ON`; the 2.x line after it removes the old spelling. `pytest.ini` turns a
`SADeprecationWarning` into an error, so building the statement with the old
spelling fails here, and this test also pins that the statement is still
`DISTINCT ON` (the property the repository relies on to avoid an N+1).
"""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy.dialects import postgresql

from adapters.web.repositories import ReconciliationJobRepository


class _NoRows:
    def mappings(self) -> "_NoRows":
        return self

    def all(self) -> list:
        return []


class _CapturingConnection:
    def __init__(self) -> None:
        self.statements: list = []

    def execute(self, statement):
        self.statements.append(statement)
        return _NoRows()


def test_latest_stamps_is_a_single_distinct_on_statement() -> None:
    connection = _CapturingConnection()
    repository = ReconciliationJobRepository(
        connection, lease_seconds=60, max_attempts=3
    )

    assert repository.latest_stamps([uuid4(), None]) == {}

    assert len(connection.statements) == 1
    sql = str(connection.statements[0].compile(dialect=postgresql.dialect()))
    assert "DISTINCT ON (reconciliation_jobs.snapshot_id)" in sql
    assert "reconciliation_jobs.snapshot_id IN" in sql
