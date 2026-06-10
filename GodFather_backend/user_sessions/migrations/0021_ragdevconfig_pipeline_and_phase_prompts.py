from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_sessions", "0020_ragdevconfig"),
    ]

    operations = [
        migrations.AddField(
            model_name="ragdevconfig",
            name="active_pipeline",
            field=models.CharField(
                choices=[("rag_v1", "RAG v1"), ("rag_v2", "RAG v2")],
                default="rag_v1",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="ragdevconfig",
            name="phase_1_master_prompt",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="ragdevconfig",
            name="phase_2_master_prompt",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="ragdevconfig",
            name="phase_3_master_prompt",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="ragdevconfig",
            name="phase_4_master_prompt",
            field=models.TextField(blank=True, default=""),
        ),
    ]
