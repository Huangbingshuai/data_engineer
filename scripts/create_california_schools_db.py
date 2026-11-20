#!/usr/bin/env python3
"""Build a real, school-level California education DuckDB from the bundled source."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DB = ROOT / "sample_data" / "california_schools" / "california_schools.sqlite"
DEFAULT_OUTPUT = ROOT / "sample_data" / "california_schools_real.duckdb"

# Contact details and administrator names are intentionally excluded from the
# schools table; all remaining fields describe schools or aggregate outcomes.
SCHOOL_COLUMNS = {
    "schools": [
        "CDSCode", "NCESDist", "NCESSchool", "StatusType", "County", "District", "School",
        "City", "Zip", "State", "OpenDate", "ClosedDate", "Charter", "CharterNum",
        "FundingType", "DOC", "DOCType", "SOC", "SOCType", "EdOpsCode", "EdOpsName",
        "EILCode", "EILName", "GSoffered", "GSserved", "Virtual", "Magnet", "Latitude",
        "Longitude", "LastUpdate",
    ],
    "frpm": None,
    "satscores": None,
}

METADATA = [
    ("dataset_name", "California Schools and Education Outcomes"),
    ("source_file", "sample_data/california_schools/california_schools.sqlite"),
    ("source_period", "FRPM: 2014-2015; SAT: historical CDE data"),
    ("primary_sources", "California Department of Education (CDE) public data files"),
    ("frpm_source_url", "https://www.cde.ca.gov/DS/ad/filessp.asp"),
    ("sat_source_url", "https://www.cde.ca.gov/re/pr/satdata.asp"),
    ("school_directory_source_url", "https://www.cde.ca.gov/Ds/"),
    (
        "transformation",
        "Copied source rows into DuckDB. Omitted school street/mailing addresses, phone, website, and administrator names/emails.",
    ),
    ("privacy_scope", "School-level aggregates and directory fields; no student-level records."),
]


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def duckdb_type(sqlite_type: str) -> str:
    normalized = sqlite_type.upper()
    if "INT" in normalized:
        return "BIGINT"
    if any(kind in normalized for kind in ("REAL", "FLOA", "DOUB")):
        return "DOUBLE"
    return "VARCHAR"


def transfer_table(source: sqlite3.Connection, target: duckdb.DuckDBPyConnection, table: str) -> int:
    source_columns = source.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall()
    requested_columns = SCHOOL_COLUMNS[table]
    if requested_columns is None:
        requested_columns = [column[1] for column in source_columns]
    column_types = {column[1]: column[2] for column in source_columns}
    columns_sql = ", ".join(
        f"{quote_identifier(column)} {duckdb_type(column_types[column])}" for column in requested_columns
    )
    target.execute(f"CREATE TABLE {quote_identifier(table)} ({columns_sql})")

    select_sql = ", ".join(quote_identifier(column) for column in requested_columns)
    insert_sql = f"INSERT INTO {quote_identifier(table)} VALUES ({', '.join('?' for _ in requested_columns)})"
    cursor = source.execute(f"SELECT {select_sql} FROM {quote_identifier(table)}")
    count = 0
    while rows := cursor.fetchmany(5000):
        target.executemany(insert_sql, rows)
        count += len(rows)
    return count


def make_database(output: Path, source_path: Path = SOURCE_DB) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing database: {output}")
    if not source_path.is_file():
        raise FileNotFoundError(f"Source SQLite database not found: {source_path}")

    output.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(f"file:{source_path.resolve()}?mode=ro", uri=True)
    target = duckdb.connect(str(output))
    try:
        target.execute("BEGIN TRANSACTION")
        row_counts = {table: transfer_table(source, target, table) for table in SCHOOL_COLUMNS}
        target.execute("CREATE TABLE dataset_metadata (key VARCHAR PRIMARY KEY, value VARCHAR NOT NULL)")
        target.executemany("INSERT INTO dataset_metadata VALUES (?, ?)", METADATA)

        checks = {
            "source row counts": all(
                target.execute(f"SELECT COUNT(*) FROM {quote_identifier(table)}").fetchone()[0] == count
                for table, count in row_counts.items()
            ),
            "school keys": target.execute(
                "SELECT COUNT(*) = COUNT(DISTINCT CDSCode) AND COUNT(CDSCode) = COUNT(*) FROM schools"
            ).fetchone()[0],
            "FRPM school links": target.execute(
                "SELECT COUNT(*) FROM frpm f LEFT JOIN schools s ON f.CDSCode = s.CDSCode WHERE s.CDSCode IS NULL"
            ).fetchone()[0]
            == 0,
            "FRPM period": target.execute(
                'SELECT COUNT(DISTINCT "Academic Year") = 1 AND MIN("Academic Year") = \'2014-2015\' FROM frpm'
            ).fetchone()[0],
            "SAT row types": target.execute("SELECT COUNT(*) FROM satscores WHERE rtype NOT IN ('D', 'S')").fetchone()[0]
            == 0,
            "no staff contact fields": not any(
                column[1].lower().startswith("adm") or column[1].lower() in {"phone", "website", "street"}
                for column in target.execute("PRAGMA table_info('schools')").fetchall()
            ),
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            raise RuntimeError("Data validation failed: " + ", ".join(failed))
        target.execute("COMMIT")

        print(f"Created {output}")
        for table, count in row_counts.items():
            print(f"{table}: {count:,} rows")
        print(f"Validation passed: {', '.join(checks)}")
    except Exception:
        try:
            target.execute("ROLLBACK")
        except Exception:
            pass
        target.close()
        output.unlink(missing_ok=True)
        raise
    finally:
        source.close()
        try:
            target.close()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    make_database(args.output.expanduser().resolve(), args.source.expanduser().resolve())


if __name__ == "__main__":
    main()
