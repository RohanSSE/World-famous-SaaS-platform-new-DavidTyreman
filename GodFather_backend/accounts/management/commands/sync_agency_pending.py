"""Align agency owners with inactive agency orgs (pending until admin activates)."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from accounts.models import Agency

User = get_user_model()


class Command(BaseCommand):
    help = "Set agency owners inactive when their agency org is inactive."

    def handle(self, *args, **options):
        fixed_users = 0
        fixed_agencies = 0

        for agency in Agency.objects.select_related("owner").filter(owner__isnull=False):
            owner = agency.owner
            if not owner.is_active and agency.is_active:
                Agency.objects.filter(pk=agency.pk).update(is_active=False)
                fixed_agencies += 1
            elif owner.role and owner.role.name.lower() == "agency":
                if not agency.is_active and owner.is_active:
                    User.objects.filter(pk=owner.pk).update(is_active=False)
                    fixed_users += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced pending state: {fixed_users} owner(s), {fixed_agencies} agency org(s)."
            )
        )
