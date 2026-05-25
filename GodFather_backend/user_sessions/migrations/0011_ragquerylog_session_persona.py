# Generated migration for RAG observability + session persona

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("user_sessions", "0010_alter_question_stage"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="persona",
            field=models.CharField(
                blank=True,
                choices=[
                    ("default", "Default"),
                    ("founder", "Founder"),
                    ("investor", "Investor"),
                    ("agency", "Agency"),
                ],
                default="default",
                help_text="Boosts retrieval toward persona-relevant knowledge categories",
                max_length=32,
            ),
        ),
        migrations.CreateModel(
            name="RAGQueryLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.IntegerField(blank=True, null=True)),
                ("query", models.TextField()),
                ("agent_id", models.CharField(default="default", max_length=64)),
                ("top_chunks", models.JSONField(blank=True, default=list)),
                ("latency_ms", models.PositiveIntegerField(default=0)),
                ("token_usage", models.JSONField(blank=True, default=dict)),
                ("cache_hit", models.BooleanField(default=False)),
                ("context_length", models.PositiveIntegerField(default=0)),
                ("answer_preview", models.TextField(blank=True, default="")),
                ("debug_payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="rag_query_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["-created_at"], name="user_sessio_created_8a1b2c_idx"),
                    models.Index(fields=["user", "-created_at"], name="user_sessio_user_id_9d2e3f_idx"),
                ],
            },
        ),
    ]
