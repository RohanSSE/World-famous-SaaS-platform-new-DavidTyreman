#!/usr/bin/env python
"""
Verify the Django backend is reading from the configured SQLite database.
Run from project root: python utils/check_db.py
"""
import os
import sys

# Project root = parent of utils/
def _project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add project root so Django finds project.settings
if __name__ == "__main__":
    root = _project_root()
    sys.path.insert(0, root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

    import django
    django.setup()

from django.conf import settings
from django.db import connection


def run_check():
    db = settings.DATABASES["default"]
    engine = db["ENGINE"]
    name = db["NAME"]

    # Resolve path if it's a Path object
    if hasattr(name, "resolve"):
        name = str(name.resolve())
    path_display = name

    in_memory = name == ":memory:"
    print("=" * 60)
    print("BACKEND DATABASE CHECK")
    print("=" * 60)
    print(f"Engine:     {engine}")
    print(f"Database:   {path_display}")
    print(f"In-memory:  {in_memory}")
    if not in_memory and os.path.isfile(name):
        size = os.path.getsize(name)
        print(f"File size:  {size:,} bytes")
    print()

    # Use the same connection the backend uses
    with connection.cursor() as cursor:
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"SQLite version: {version}")

    # Count tables
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables:     {len(tables)}")
    print()

    # Query key models to prove we're reading from this DB
    from django.contrib.auth import get_user_model
    from django.contrib.contenttypes.models import ContentType

    User = get_user_model()
    counts = []

    try:
        user_count = User.objects.count()
        counts.append(("accounts.User", user_count))
    except Exception as e:
        counts.append(("accounts.User", f"Error: {e}"))

    try:
        from user_sessions.models import Session as BrandSession, Question, Answer
        session_count = BrandSession.objects.count()
        question_count = Question.objects.count()
        answer_count = Answer.objects.count()
        counts.append(("user_sessions.Session", session_count))
        counts.append(("user_sessions.Question", question_count))
        counts.append(("user_sessions.Answer", answer_count))
    except Exception as e:
        counts.append(("user_sessions.*", f"Error: {e}"))

    try:
        ct_count = ContentType.objects.count()
        counts.append(("contenttypes.ContentType", ct_count))
    except Exception as e:
        counts.append(("contenttypes.ContentType", f"Error: {e}"))

    print("Model row counts (backend reading from above database):")
    print("-" * 60)
    for model_name, count in counts:
        print(f"  {model_name}: {count}")
    print()

    # Sample: first 3 users
    try:
        users = list(User.objects.values_list("email", "is_active")[:3])
        if users:
            print("Sample users (email, is_active):")
            for email, active in users:
                print(f"  - {email!r} (active={active})")
        else:
            print("No users in database.")
    except Exception as e:
        print(f"Sample users: {e}")
    print()

    print("=" * 60)
    print("Result: Backend is reading from the configured SQLite database.")
    print("=" * 60)


if __name__ == "__main__":
    run_check()
