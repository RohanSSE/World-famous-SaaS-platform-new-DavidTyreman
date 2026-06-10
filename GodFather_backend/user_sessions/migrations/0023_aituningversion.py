from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("user_sessions", "0022_ragphaseartifact"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AITuningVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version_number", models.PositiveIntegerField(db_index=True, default=1)),
                (
                    "action",
                    models.CharField(
                        choices=[("save", "Save"), ("train", "Train"), ("load_default", "Load Default")],
                        default="save",
                        max_length=24,
                    ),
                ),
                (
                    "section_key",
                    models.CharField(
                        choices=[
                            ("phase_1_master_prompt", "Discovery"),
                            ("phase_2_master_prompt", "BrandBook"),
                            ("phase_3_master_prompt", "Content Generation"),
                            ("phase_4_master_prompt", "Ongoing Guidance"),
                            ("global", "Global"),
                        ],
                        default="global",
                        max_length=40,
                    ),
                ),
                ("active_pipeline", models.CharField(default="rag_v1", max_length=16)),
                ("snapshot", models.JSONField(blank=True, default=dict)),
                ("is_default_template", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ai_tuning_versions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="aituningversion",
            index=models.Index(fields=["section_key", "created_at"], name="user_sessio_section_3f5964_idx"),
        ),
        migrations.AddIndex(
            model_name="aituningversion",
            index=models.Index(fields=["is_default_template", "created_at"], name="user_sessio_is_defa_54ab5f_idx"),
        ),
    ]
