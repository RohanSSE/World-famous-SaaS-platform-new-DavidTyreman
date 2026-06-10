from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_subscriptionplan_usersubscription"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscriptionplan",
            name="question_gate_after",
            field=models.PositiveIntegerField(
                default=8,
                help_text="Users must subscribe after this many answered journey questions.",
            ),
        ),
    ]