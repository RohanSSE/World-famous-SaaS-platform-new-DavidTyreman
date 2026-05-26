from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_sessions", "0015_evaluation_models_memory_types"),
    ]

    operations = [
        migrations.AddField(
            model_name="brandmemory",
            name="is_pinned",
            field=models.BooleanField(
                default=False,
                help_text="Pinned memories never decay (manifesto truths, core positioning)",
            ),
        ),
        migrations.AddField(
            model_name="brandmemory",
            name="retrieval_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
