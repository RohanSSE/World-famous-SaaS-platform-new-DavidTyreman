from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_sessions", "0013_brandmemory_pgvector"),
    ]

    operations = [
        migrations.AddField(
            model_name="brandmemory",
            name="confidence",
            field=models.FloatField(default=0.5),
        ),
        migrations.AddField(
            model_name="brandmemory",
            name="value",
            field=models.JSONField(blank=True, default=dict),
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
                ],
                default="brand_fact",
                max_length=32,
            ),
        ),
    ]
