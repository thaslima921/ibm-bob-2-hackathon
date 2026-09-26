"""
User manager module — intentionally contains logic bugs and missing null checks.

Known issues:
  - assign_role: logic bug — 'moderator' role never gets assigned (wrong elif chain)
  - get_user_display_name: crashes on None first_name without guard
  - deactivate_user: missing check — can deactivate already-inactive users silently
  - calculate_user_score: integer division truncates score incorrectly
"""


VALID_ROLES = {"admin", "editor", "moderator", "viewer"}


def create_user(username: str, email: str, role: str = "viewer") -> dict:
    """Create a new user record."""
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}")
    return {
        "username": username,
        "email": email,
        "role": role,
        "active": True,
        "score": 0,
        "first_name": None,
        "last_name": None,
    }


def assign_role(user: dict, new_role: str) -> dict:
    """Assign a new role to a user.

    BUG: The elif chain never reaches 'moderator' — the condition is wrong.
    'moderator' should be handled but the check for editor swallows it.
    """
    if new_role == "admin":
        user["role"] = "admin"
    elif new_role == "editor" or new_role == "moderator":  # BUG: moderator merged with editor
        user["role"] = "editor"  # BUG: moderator users silently become editors
    elif new_role == "viewer":
        user["role"] = "viewer"
    else:
        raise ValueError(f"Unknown role: {new_role}")
    return user


def get_user_display_name(user: dict) -> str:
    """Return a formatted display name.

    BUG: Does not guard against None first_name — crashes with AttributeError.
    """
    return f"{user['first_name'].strip()} {user['last_name'].strip()}"  # BUG: NoneType.strip()


def deactivate_user(user: dict) -> dict:
    """Deactivate a user account.

    BUG: No check whether user is already inactive — silent no-op that returns
    success even when the user was never active, making audit logs misleading.
    """
    user["active"] = False  # BUG: no guard for already-inactive state
    return user


def calculate_user_score(actions: int, weight: float) -> float:
    """Calculate a user's activity score.

    BUG: Uses integer division (//) which silently truncates fractional scores.
    """
    raw = actions * weight
    return raw // 1  # BUG: should be round(raw, 2) or just raw


def get_active_users(users: list) -> list:
    """Return only active users."""
    return [u for u in users if u.get("active")]
