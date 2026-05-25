# Generated for Enterprise Reliability sprint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_sessions", "0017_airequesttrace"),
    ]

    operations = [
        migrations.AddField(
            model_name="airequesttrace",
            name="confidence_score",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="airequesttrace",
            name="reasoning_trace",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
