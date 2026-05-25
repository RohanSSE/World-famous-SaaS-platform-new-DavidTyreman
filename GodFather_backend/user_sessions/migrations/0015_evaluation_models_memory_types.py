# Generated for Phase 15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("user_sessions", "0014_brandmemory_value_confidence"),
    ]

    operations = [
        migrations.CreateModel(
            name="EvaluationRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("run_type", models.CharField(default="nightly", max_length=32)),
                ("status", models.CharField(default="completed", max_length=16)),
                ("total_cases", models.PositiveIntegerField(default=0)),
                ("passed_cases", models.PositiveIntegerField(default=0)),
                ("avg_groundedness", models.FloatField(default=0)),
                ("avg_hallucination_risk", models.FloatField(default=0)),
                ("avg_citation_accuracy", models.FloatField(default=0)),
                ("avg_retrieval_precision", models.FloatField(default=0)),
                ("summary", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="EvaluationResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("case_id", models.CharField(db_index=True, max_length=64)),
                ("groundedness", models.FloatField(default=0)),
                ("hallucination_risk", models.FloatField(default=0)),
                ("citation_accuracy", models.FloatField(default=0)),
                ("tone_consistent", models.BooleanField(default=True)),
                ("retrieval_precision", models.FloatField(default=0)),
                ("passed", models.BooleanField(default=False)),
                ("metrics", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="user_sessions.evaluationrun",
                    ),
                ),
            ],
            options={
                "ordering": ["case_id"],
                "indexes": [models.Index(fields=["run", "case_id"], name="user_sessio_run_id_8f3a2c_idx")],
            },
        ),
        migrations.AlterField(
            model_name="brandmemory",
            name="memory_type",
            field=models.CharField(
                choices=[
                    ("brand_fact", "Brand Fact"),
                    ("preference", "Preference"),
                    ("tone", "Tone"),
                    ("decision", "Decision"),
                    ("rejected_strategy", "Rejected Strategy"),
                    ("persona_note", "Persona Note"),
                    ("manifesto_evolution", "Manifesto Evolution"),
                    ("emotional_language", "Emotional Language"),
                    ("competitor_mention", "Competitor Mention"),
                    ("strategic_priority", "Strategic Priority"),
                    ("brand_voice", "Brand Voice"),
                    ("emotional_pattern", "Emotional Pattern"),
                    ("competitor_positioning", "Competitor Positioning"),
                    ("founder_personality", "Founder Personality"),
                    ("audience_psychology", "Audience Psychology"),
                ],
                default="brand_fact",
                max_length=32,
            ),
        ),
    ]
