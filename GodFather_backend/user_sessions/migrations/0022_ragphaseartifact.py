from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("user_sessions", "0021_ragdevconfig_pipeline_and_phase_prompts"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RAGPhaseArtifact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "phase_key",
                    models.CharField(
                        choices=[
                            ("phase_1", "Phase 1 Discovery"),
                            ("phase_2", "Phase 2 Brand Book and Playbook"),
                            ("phase_3", "Phase 3 Brand Promotion"),
                            ("phase_4", "Phase 4 Strategic Guidance and Content Creation"),
                        ],
                        max_length=16,
                    ),
                ),
                ("artifact", models.JSONField(blank=True, default=dict)),
                ("summary", models.TextField(blank=True, default="")),
                ("source_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rag_phase_artifacts",
                        to="user_sessions.session",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_rag_phase_artifacts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["phase_key", "-updated_at"],
                "unique_together": {("session", "phase_key")},
            },
        ),
        migrations.AddIndex(
            model_name="ragphaseartifact",
            index=models.Index(fields=["session", "phase_key"], name="user_sessions_ragphase_session_322ca2_idx"),
        ),
    ]
