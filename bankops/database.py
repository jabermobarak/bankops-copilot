"""Atomic seed; runtime tools open a separate, read-only connection per call."""

import csv
import os
import sqlite3
import tempfile
from contextlib import closing, contextmanager
from pathlib import Path


def seed_database(root: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="bankops-", suffix=".sqlite", dir=target.parent)
    os.close(fd)
    try:
        # sqlite3's context manager commits/rolls back, but does not close.
        # Close before replace/unlink: Windows forbids renaming an open file.
        with closing(sqlite3.connect(temporary)) as con, con:
            con.executescript((root / "data/schema.sql").read_text(encoding="utf-8"))
            for table in ("balances", "cashflows", "exposures"):
                with (root / f"data/{table}.csv").open(newline="", encoding="utf-8") as source:
                    reader = csv.DictReader(source)
                    columns = reader.fieldnames
                    placeholders = ",".join("?" for _ in columns)
                    # Table and column identifiers are repository-controlled, never user input.
                    con.executemany(
                        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                        [tuple(row[c] for c in columns) for row in reader],
                    )
            con.execute("CREATE INDEX flow_dates ON cashflows(as_of, due_date)")
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def readonly(path: Path):
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=ON")
        yield con
