from django.db import migrations
import os


def _use_pgvector() -> bool:
    return os.environ.get("PGVECTOR_ENABLED", "false").lower() in ("1", "true", "yes")


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;",
        ),
    ] if _use_pgvector() else []
