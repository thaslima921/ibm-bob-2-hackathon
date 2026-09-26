"""Tests for auth module — success path only (testing gap intentional)."""
import pytest
from sample_project.app.auth import hash_password, verify_password, login, generate_token


FAKE_USER_STORE = {
    "alice": {"password_hash": hash_password("correcthorsebatterystaple"), "role": "admin"},
    "bob": {"password_hash": hash_password("hunter2"), "role": "viewer"},
}


def test_hash_password_returns_string():
    result = hash_password("mypassword")
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex length


def test_verify_password_correct():
    hashed = hash_password("secret")
    assert verify_password("secret", hashed) is True


def test_login_success():
    result = login("alice", "correcthorsebatterystaple", FAKE_USER_STORE)
    assert result is not None
    assert result["username"] == "alice"
    assert "token" in result


def test_generate_token_returns_string():
    token = generate_token("alice")
    assert isinstance(token, str)
    assert len(token) > 0


# TESTING GAP: no test for login with wrong password (should return None)
# TESTING GAP: no test for login with unknown username
# TESTING GAP: no test verifying token is NOT predictable / reusable
# TESTING GAP: no test for verify_password timing-attack resistance
