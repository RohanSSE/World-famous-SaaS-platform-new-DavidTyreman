# Generated

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("user_sessions", "0011_ragquerylog_session_persona"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIUsageLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.IntegerField(blank=True, null=True)),
                ("agent_id", models.CharField(default="default", max_length=64)),
                ("endpoint", models.CharField(blank=True, default="", max_length=128)),
                ("prompt_tokens", models.PositiveIntegerField(default=0)),
                ("completion_tokens", models.PositiveIntegerField(default=0)),
                ("embedding_tokens", models.PositiveIntegerField(default=0)),
                ("total_tokens", models.PositiveIntegerField(default=0)),
                ("estimated_cost_usd", models.DecimalField(decimal_places=6, default=0, max_digits=10)),
                ("latency_ms", models.PositiveIntegerField(default=0)),
                ("cache_hit", models.BooleanField(default=False)),
                ("degraded", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ai_usage_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="BrandMemory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("memory_type", models.CharField(choices=[("brand_fact", "Brand Fact"), ("preference", "Preference"), ("tone", "Tone"), ("decision", "Decision"), ("rejected_strategy", "Rejected Strategy"), ("persona_note", "Persona Note")], default="brand_fact", max_length=32)),
                ("key", models.CharField(max_length=255)),
                ("content", models.TextField()),
                ("weight", models.FloatField(default=1.0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="brand_memories", to="user_sessions.session")),
            ],
            options={"ordering": ["-updated_at"], "unique_together": {("session", "key")}},
        ),
        migrations.AddIndex(
            model_name="aiusagelog",
            index=models.Index(fields=["user", "-created_at"], name="user_sessio_user_ai_usage_idx"),
        ),
    ]
