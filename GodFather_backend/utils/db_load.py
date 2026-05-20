# Load Django fixture (db_dump.json) into SQLite with uniform schema to prevent schema drift.
# Normalizes per-model schema (same fields for every record) so schema drift does not occur.
# Uses pandas for normalization when available (pip install pandas) for large fixtures.
# Run from project root: python utils/db_load.py

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, List, Optional, Tuple

try:
    import pandas as pd
except ImportError:
    pd = None

# Project root (parent of utils/)
def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Django model label -> actual DB table name (overrides where Django uses custom db_table)
MODEL_TO_TABLE = {
    "admin.logentry": "django_admin_log",
    "contenttypes.contenttype": "django_content_type",
    "sessions.session": "django_session",
}


def _model_to_table(model_label: str) -> str:
    """Convert Django model label (app_label.model_name) to database table name."""
    if model_label in MODEL_TO_TABLE:
        return MODEL_TO_TABLE[model_label]
    app_label, model_name = model_label.split(".", 1)
    return f"{app_label}_{model_name}"


def _normalize_fixture_to_uniform_schema(data: List[dict]) -> List[dict]:
    """
    Ensure every record of the same model has the same set of field keys (fill missing with None).
    Prevents schema drift when different records have different fields.
    Uses pandas when available for efficiency on large fixtures.
    """
    if not data:
        return data

    if pd is not None:
        df = pd.DataFrame(data)
        if "model" in df.columns and "fields" in df.columns:
            model_schemas = df.groupby("model")["fields"].apply(
                lambda ser: sorted(set().union(*(f.keys() for f in ser)))
            ).to_dict()
            out = []
            for _, row in df.iterrows():
                rec = {"model": row["model"], "pk": row["pk"], "fields": dict(row["fields"])}
                schema = model_schemas.get(rec["model"], [])
                for k in schema:
                    rec["fields"].setdefault(k, None)
                rec["fields"] = {k: rec["fields"][k] for k in schema}
                out.append(rec)
            return out

    # Pure Python path
    model_schemas = {}
    for item in data:
        model = item.get("model")
        if model is None:
            continue
        fields = item.get("fields") or {}
        if model not in model_schemas:
            model_schemas[model] = set()
        model_schemas[model].update(fields.keys())
    for model in model_schemas:
        model_schemas[model] = sorted(model_schemas[model])

    out = []
    for item in data:
        model = item.get("model")
        pk = item.get("pk")
        fields = dict(item.get("fields") or {})
        if model is None:
            out.append(item)
            continue
        schema = model_schemas.get(model, [])
        for k in schema:
            fields.setdefault(k, None)
        out.append({"model": model, "pk": pk, "fields": {k: fields[k] for k in schema}})
    return out


def _serialize_value(val):
    """Serialize a Python value for SQLite (JSON, bool, None, datetime)."""
    if val is None:
        return None
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    if hasattr(val, "isoformat"):  # date, datetime
        return val.isoformat()
    return val


def _get_table_columns(cursor: sqlite3.Cursor, table: str) -> Tuple[list, Optional[str]]:
    """
    Return (list of column names, primary key column name or None).
    Django uses 'id' for most tables; sessions.session uses 'session_key'.
    """
    cursor.execute(f'PRAGMA table_info("{table}")')
    rows = cursor.fetchall()
    # Each row: (cid, name, type, notnull, dflt_value, pk)
    columns = [r[1] for r in rows]
    pk_col = None
    for r in rows:
        if r[5]:  # pk is the 6th element (1-based: pk)
            pk_col = r[1]
            break
    return columns, pk_col


def load_fixture_into_sqlite(
    fixture_path: str,
    db_path: str = "db.sqlite3",
    normalize_schema: bool = True,
    write_normalized_fixture: Optional[str] = None,
) -> None:
    """
    Load a Django fixture JSON into the SQLite database with schema-safe inserts.

    - Reads fixture in Django format: [{"model": "app.model", "pk": ..., "fields": {...}}, ...]
    - Normalizes so each model has a uniform set of fields (no drift)
    - Only inserts columns that exist in the target table (avoids drift vs DB)
    - Optionally writes the normalized fixture to a file for reuse

    Args:
        fixture_path: Path to db_dump.json (or any Django fixture).
        db_path: Path to SQLite database file.
        normalize_schema: If True, ensure uniform fields per model using pandas.
        write_normalized_fixture: If set, write normalized fixture to this path (e.g. db_dump_normalized.json).
    """
    path = Path(fixture_path)
    if not path.is_file():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Fixture JSON must be a list of objects with 'model', 'pk', 'fields'.")

    if normalize_schema:
        data = _normalize_fixture_to_uniform_schema(data)

    if write_normalized_fixture:
        with open(write_normalized_fixture, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Wrote normalized fixture to {write_normalized_fixture}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Track table -> (columns list, pk column name)
    table_columns_cache = {}
    inserted = 0
    skipped_tables = set()
    errors = []

    for item in data:
        model_label = item.get("model")
        pk = item.get("pk")
        fields = item.get("fields")
        if model_label is None or fields is None:
            errors.append(f"Skip: missing 'model' or 'fields': {item}")
            continue

        table = _model_to_table(model_label)
        if table not in table_columns_cache:
            try:
                table_columns_cache[table] = _get_table_columns(cursor, table)
            except sqlite3.OperationalError:
                skipped_tables.add(table)
                continue
        columns, pk_col = table_columns_cache[table]
        if not columns:
            skipped_tables.add(table)
            continue

        # Map fixture pk to table's primary key column (id or e.g. session_key)
        col_set = set(columns)
        row = {}
        if pk_col:
            row[pk_col] = _serialize_value(pk)
        for k, v in fields.items():
            if k in col_set:
                row[k] = _serialize_value(v)
            # Django stores ForeignKey "user" as column "user_id"
            elif k + "_id" in col_set:
                row[k + "_id"] = _serialize_value(v)
        if not row:
            continue

        insert_cols = [c for c in columns if c in row]
        if not insert_cols:
            continue
        placeholders = ", ".join("?" for _ in insert_cols)
        names = ", ".join(f'"{c}"' for c in insert_cols)
        values = [row[c] for c in insert_cols]
        try:
            cursor.execute(
                f'INSERT OR REPLACE INTO "{table}" ({names}) VALUES ({placeholders})',
                values,
            )
            inserted += 1
        except sqlite3.IntegrityError as e:
            errors.append(f"{table} pk={pk}: {e}")
        except Exception as e:
            errors.append(f"{table} pk={pk}: {e}")

    conn.commit()
    conn.close()

    if skipped_tables:
        print(f"Skipped (table not found or no columns): {sorted(skipped_tables)}")
    if errors:
        for err in errors[:20]:
            print(err)
        if len(errors) > 20:
            print(f"... and {len(errors) - 20} more errors")
    print(f"Database loaded: {inserted} rows inserted from {fixture_path}")


def normalize_fixture_file(
    input_path: str = "db_dump.json",
    output_path: Optional[str] = None,
) -> None:
    """
    Read a Django fixture, normalize to uniform schema per model (using pandas),
    and write back. If output_path is None, overwrites input_path.
    """
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Fixture JSON must be a list of objects.")
    data = _normalize_fixture_to_uniform_schema(data)
    out = output_path or input_path
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Normalized fixture written to {out}")


if __name__ == "__main__":
    import argparse

    root = _project_root()
    default_fixture = os.path.join(root, "db_dump.json")
    default_db = os.path.join(root, "db.sqlite3")

    parser = argparse.ArgumentParser(description="Load Django fixture into SQLite with uniform schema (no drift).")
    parser.add_argument(
        "fixture",
        nargs="?",
        default=default_fixture,
        help=f"Path to fixture JSON (default: {default_fixture})",
    )
    parser.add_argument("--db", default=default_db, help=f"Path to SQLite database (default: {default_db})")
    parser.add_argument("--no-normalize", action="store_true", help="Skip pandas normalization (not recommended)")
    parser.add_argument(
        "--write-normalized",
        metavar="PATH",
        default=None,
        help="Write normalized fixture to this file (e.g. db_dump_normalized.json)",
    )
    parser.add_argument(
        "--normalize-only",
        action="store_true",
        help="Only normalize the fixture file and exit (no DB load)",
    )
    args = parser.parse_args()

    fixture_path = args.fixture if os.path.isabs(args.fixture) else os.path.join(root, args.fixture)
    db_path = args.db if os.path.isabs(args.db) else os.path.join(root, args.db)

    if args.normalize_only:
        normalize_fixture_file(fixture_path, args.write_normalized or fixture_path)
    else:
        load_fixture_into_sqlite(
            fixture_path=fixture_path,
            db_path=db_path,
            normalize_schema=not args.no_normalize,
            write_normalized_fixture=args.write_normalized,
        )
