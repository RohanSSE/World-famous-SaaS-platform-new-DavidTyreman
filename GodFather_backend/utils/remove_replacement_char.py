#!/usr/bin/env python
"""
Remove the Unicode replacement character (U+FFFD) from all text columns in db.sqlite3.
Run from project root: python utils/remove_replacement_char.py
"""
import os
import sqlite3

# The character to remove (Unicode replacement character, often from encoding errors)
BAD_CHAR = "\ufffd"

# Database path: project root / db.sqlite3
def _project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(_project_root(), "db.sqlite3")


def is_text_type(sqlite_type: str) -> bool:
    if not sqlite_type:
        return False
    t = (sqlite_type or "").upper()
    if "TEXT" in t or "CHAR" in t or "CLOB" in t:
        return True
    if "INT" in t or "REAL" in t or "FLOAT" in t or "NUM" in t or "BLOB" in t:
        return False
    return True  # unknown type, treat as possibly text


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tables = [r[0] for r in cursor.fetchall()]

    total_updates = 0
    for table in tables:
        cursor.execute(f'PRAGMA table_info("{table}")')
        columns = cursor.fetchall()
        for col in columns:
            cid, name, type_, notnull, dflt, pk = col
            if not is_text_type(type_):
                continue
            try:
                # Only update rows that contain the character
                cursor.execute(
                    f'UPDATE "{table}" SET "{name}" = REPLACE("{name}", ?, ?) WHERE "{name}" LIKE \'%\' || ? || \'%\'',
                    (BAD_CHAR, "", BAD_CHAR),
                )
                if cursor.rowcount > 0:
                    total_updates += cursor.rowcount
                    print(f"  {table}.{name}: {cursor.rowcount} row(s) updated")
            except sqlite3.OperationalError as e:
                print(f"  {table}.{name}: skip - {e}")

    conn.commit()
    conn.close()
    print(f"\nDone. Total rows updated: {total_updates}")


if __name__ == "__main__":
    main()
