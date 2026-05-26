from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("user_sessions", "0016_brandmemory_pinned_retrieval_count"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIRequestTrace",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.IntegerField(blank=True, null=True)),
                ("query", models.TextField(blank=True, default="")),
                ("agent_id", models.CharField(default="default", max_length=64)),
                ("embedding_ms", models.PositiveIntegerField(default=0)),
                ("retrieval_ms", models.PositiveIntegerField(default=0)),
                ("rerank_ms", models.PositiveIntegerField(default=0)),
                ("generation_ms", models.PositiveIntegerField(default=0)),
                ("verification_ms", models.PositiveIntegerField(default=0)),
                ("total_ms", models.PositiveIntegerField(default=0)),
                ("retrieval_confidence", models.CharField(blank=True, default="", max_length=32)),
                ("hallucination_risk", models.FloatField(blank=True, null=True)),
                ("pipeline", models.CharField(blank=True, default="", max_length=64)),
                ("stages", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="airequesttrace",
            index=models.Index(fields=["-created_at"], name="user_sessio_created_a7f1c2_idx"),
        ),
        migrations.AddIndex(
            model_name="airequesttrace",
            index=models.Index(fields=["agent_id", "-created_at"], name="user_sessio_agent_i_8b3d4e_idx"),
        ),
    ]
