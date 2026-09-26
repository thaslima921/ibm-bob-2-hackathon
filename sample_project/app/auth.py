"""
Authentication module — intentionally contains security issues for ChangeGuard demo.

Known issues:
  - SECRET_KEY is hardcoded (should come from environment variable)
  - verify_password uses == comparison (timing-attack vulnerable)
  - login logs plaintext password to stdout
  - generate_token produces a weak, predictable token
"""
import hashlib
import time
import logging

logger = logging.getLogger(__name__)

# SECURITY: Hardcoded secret key — should be loaded from environment variable
SECRET_KEY = "super_secret_key_1234"  # SECURITY ISSUE


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    SECURITY: Uses == for string comparison — vulnerable to timing attacks.
    Should use hmac.compare_digest() instead.
    """
    return hash_password(plain_password) == hashed_password  # SECURITY ISSUE


def login(username: str, password: str, user_store: dict) -> dict | None:
    """Authenticate a user and return a session token.

    SECURITY: Logs the plaintext password — a serious credential leak.
    """
    logger.info(f"Login attempt for {username} with password {password}")  # SECURITY ISSUE
    if username not in user_store:
        return None
    stored_hash = user_store[username]["password_hash"]
    if verify_password(password, stored_hash):
        token = generate_token(username)
        return {"username": username, "token": token}
    return None


def generate_token(username: str) -> str:
    """Generate a session token.

    SECURITY: Token is derived from username + current second — predictable and guessable.
    Should use secrets.token_hex(32) instead.
    """
    raw = f"{username}{SECRET_KEY}"  # SECURITY ISSUE: predictable token
    return hashlib.md5(raw.encode()).hexdigest()  # SECURITY ISSUE: MD5 is weak


def is_admin(user: dict) -> bool:
    """Check if a user has admin role."""
    return user.get("role") == "admin"
    

