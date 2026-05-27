from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from accounts.agency_utils import ensure_agency_for_user

User = get_user_model()


class Command(BaseCommand):
    help = "Create/link Agency records for users with agency role but no agency FK"

    def handle(self, *args, **options):
        qs = User.objects.filter(role__name__iexact="agency")
        linked = 0
        for user in qs:
            before = user.agency_id
            ensure_agency_for_user(user)
            user.refresh_from_db()
            if user.agency_id and user.agency_id != before:
                linked += 1
                self.stdout.write(self.style.SUCCESS(f"  Linked {user.email} -> {user.agency.name}"))
            elif user.agency_id:
                self.stdout.write(f"  OK {user.email} -> {user.agency.name}")
        self.stdout.write(self.style.SUCCESS(f"Done. {qs.count()} agency user(s) checked."))
