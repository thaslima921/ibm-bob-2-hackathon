"""
Data processor module — intentionally contains SQL injection risk and missing validation.

Known issues:
  - build_query: f-string interpolation into SQL → SQL injection
  - process_user_input: no type or length validation before processing
  - export_data: path traversal vulnerability in filename construction
"""
import sqlite3
import os


def build_query(table: str, user_filter: str) -> str:
    """Build a SQL SELECT query.

    SECURITY: Directly interpolates user_filter into SQL — SQL injection vulnerability.
    Should use parameterised queries.
    """
    # SECURITY ISSUE: SQL injection via unsanitised f-string
    return f"SELECT * FROM {table} WHERE name = '{user_filter}'"


def fetch_records(conn: sqlite3.Connection, table: str, user_filter: str) -> list:
    """Fetch records matching a filter.

    SECURITY: Passes user input directly into SQL without parameterisation.
    """
    query = build_query(table, user_filter)
    cursor = conn.execute(query)  # SECURITY ISSUE: executes injected SQL
    return cursor.fetchall()


def process_user_input(data: dict) -> dict:
    """Process and normalise user-supplied input.

    BUG: No validation — accepts any value for 'amount', including negative numbers
    and non-numeric strings which will crash downstream numeric operations.
    """
    # BUG: missing type check, missing range validation
    amount = data["amount"]  # KeyError if missing; no type guard
    label = data.get("label", "")
    return {"amount": float(amount), "label": label.strip()}


def export_data(records: list, filename: str) -> str:
    """Write records to a file in the exports directory.

    SECURITY: Path traversal — user-controlled filename can escape the export dir.
    E.g. filename='../../etc/passwd' would write outside the intended directory.
    """
    # SECURITY ISSUE: no path sanitisation
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    full_path = os.path.join(export_dir, filename)  # SECURITY ISSUE: path traversal
    with open(full_path, "w") as f:
        for record in records:
            f.write(str(record) + "\n")
    return full_path


def calculate_statistics(values: list) -> dict:
    """Return basic statistics for a list of numbers."""
    if not values:
        return {"min": None, "max": None, "mean": None, "count": 0}
    return {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "count": len(values),
    }
