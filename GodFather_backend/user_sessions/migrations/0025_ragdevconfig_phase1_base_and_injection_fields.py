from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user_sessions", "0024_merge_20260610_1657"),
    ]

    operations = [
        migrations.AddField(
            model_name="ragdevconfig",
            name="phase_1_admin_injection_criteria",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="ragdevconfig",
            name="phase_1_admin_injection_goal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="ragdevconfig",
            name="phase_1_admin_injection_prompt",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="ragdevconfig",
            name="phase_1_base_prompt",
            field=models.TextField(blank=True, default=""),
        ),
    ]
