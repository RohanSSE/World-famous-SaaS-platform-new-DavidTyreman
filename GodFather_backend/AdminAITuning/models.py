from django.conf import settings
from django.db import models


class AITuningVersion(models.Model):
    ACTION_CHOICES = [
        ("save", "Save"),
        ("train", "Train"),
        ("load_default", "Load Default"),
    ]

    SECTION_CHOICES = [
        ("phase_1_master_prompt", "Discovery"),
        ("phase_2_master_prompt", "BrandBook"),
        ("phase_3_master_prompt", "Content Generation"),
        ("phase_4_master_prompt", "Ongoing Guidance"),
        ("global", "Global"),
    ]

    version_number = models.PositiveIntegerField(default=1, db_index=True)
    action = models.CharField(max_length=24, choices=ACTION_CHOICES, default="save")
    section_key = models.CharField(max_length=40, choices=SECTION_CHOICES, default="global")
    active_pipeline = models.CharField(max_length=16, default="rag_v1")
    snapshot = models.JSONField(default=dict, blank=True)
    is_default_template = models.BooleanField(default=False, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_tuning_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "user_sessions"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["section_key", "created_at"]),
            models.Index(fields=["is_default_template", "created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            last = AITuningVersion.objects.order_by("-version_number").values_list("version_number", flat=True).first() or 0
            self.version_number = int(last) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"AITuningVersion<v{self.version_number} {self.action} {self.section_key}>"
