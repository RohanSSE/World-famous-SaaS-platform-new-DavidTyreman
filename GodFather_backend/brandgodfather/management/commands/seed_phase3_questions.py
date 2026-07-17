from django.core.management.base import BaseCommand
from django.db import transaction

from brandgodfather.services.phase3_frameworks import PHASE3_FRAMEWORKS
from user_sessions.models import Question


class Command(BaseCommand):
    help = "Seed Phase 3 ORB backing questions into DB stage 4."

    def handle(self, *args, **options):
        created = 0
        updated = 0

        with transaction.atomic():
            for index, framework_key in enumerate(sorted(PHASE3_FRAMEWORKS, key=lambda key: int(key[1:])), start=1):
                entry = PHASE3_FRAMEWORKS[framework_key]
                _, was_created = Question.objects.update_or_create(
                    stage=4,
                    order=index,
                    defaults={
                        "text": entry["question"],
                        "category": "other",
                        "is_required": True,
                        "is_active": True,
                        "placeholder": "Type your answer...",
                        "help_text": "",
                    },
                )
                created += int(was_created)
                updated += int(not was_created)

        active_count = Question.objects.filter(stage=4, is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded Phase 3 questions: created={created}, updated={updated}, active_stage4={active_count}"
            )
        )