"""Effective account activation (user + agency org for agency-role accounts)."""


def is_user_effectively_active(user):
    """
    Agency owners are only active when both the user flag and their agency org are active.
    """
    if not user or not user.is_active:
        return False

    role_name = (user.role.name if getattr(user, "role", None) else "") or ""
    if role_name.lower() != "agency":
        return True

    agency = getattr(user, "agency", None)
    if agency is None and hasattr(user, "owned_agencies"):
        agency = user.owned_agencies.first()

    if agency is None:
        return False

    return bool(
        agency.is_active
        and agency.approved_at is not None
        and user.is_active
    )
