from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="agency",
            name="approved_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Set when an admin approves this agency.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="agency",
            name="is_active",
            field=models.BooleanField(
                default=False,
                help_text="Inactive until an admin activates the agency.",
            ),
        ),
    ]
