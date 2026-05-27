"""Helpers to link agency-role users to an Agency organization record."""

from .models import Agency


def ensure_agency_for_user(user):
    """
    Ensure a user with agency role has an Agency row and user.agency FK set.
    Idempotent — safe to call on register, activate, and dashboard load.
    Returns the Agency instance or None.
    """
    if not user or not getattr(user, "is_authenticated", True):
        return None

    role_name = (user.role.name if getattr(user, "role", None) else "") or ""
    role_name = role_name.lower()
    if role_name != "agency":
        return user.agency if getattr(user, "agency", None) else None

    if user.agency_id:
        agency = user.agency
        if agency.owner_id is None:
            agency.owner = user
            agency.save(update_fields=["owner"])
        if not agency.is_active and user.is_active:
            agency.is_active = True
            agency.save(update_fields=["is_active"])
        return agency

    owned = user.owned_agencies.first()
    if owned:
        user.agency = owned
        user.save(update_fields=["agency"])
        if owned.owner_id is None:
            owned.owner = user
            owned.save(update_fields=["owner"])
        return owned

    base = (user.email or "agency").split("@")[0].replace(".", " ").replace("_", " ").strip().title()
    if not base:
        base = "Agency"
    agency_name = f"{base} Agency"
    counter = 1
    while Agency.objects.filter(name=agency_name).exists():
        agency_name = f"{base} Agency {counter}"
        counter += 1

    agency = Agency.objects.create(
        name=agency_name,
        owner=user,
        is_active=bool(user.is_active),
    )
    user.agency = agency
    user.save(update_fields=["agency"])
    return agency
