from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_sessions", "0019_rename_user_sessio_created_a7f1c2_idx_user_sessio_created_079c31_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="ai_refined_text",
            field=models.TextField(blank=True, default="", editable=False),
        ),
        migrations.AddField(
            model_name="question",
            name="ai_refined_source_hash",
            field=models.CharField(blank=True, default="", editable=False, max_length=64),
        ),
        migrations.AddField(
            model_name="question",
            name="ai_refined_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]