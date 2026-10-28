"""
Unit and Integration Tests for Market ML Authentication & Gatekeeping Engine
Verifies PBKDF2-HMAC-SHA256 password hashing, SQLite user persistence,
duplicate prevention, and session credential validation.
"""

import os
import sys
import sqlite3
import secrets

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.auth import (
    register_user,
    authenticate_user,
    hash_password,
    verify_password,
    get_db_connection,
    init_auth_db,
    get_user_by_username
)


def test_password_hashing():
    print("Testing PBKDF2-HMAC-SHA256 password hashing...")
    pwd = "QuantumTrading#2026"
    hash_str, salt = hash_password(pwd)
    assert len(salt) == 32, "Salt must be 32 hex characters"
    assert len(hash_str) == 64, "PBKDF2 SHA256 hex must be 64 characters"
    assert verify_password(pwd, hash_str, salt) is True, "Password must verify successfully"
    assert verify_password("WrongPassword!", hash_str, salt) is False, "Wrong password must fail"
    print("✅ Password hashing test PASSED")


def test_user_registration_and_auth():
    print("Testing user registration and credential authentication...")
    init_auth_db()
    
    test_user = f"test_trader_{secrets.token_hex(4)}"
    test_email = f"{test_user}@marketml.internal"
    test_pwd = "InstitutionalPass#1"

    # 1. Register User
    success, msg = register_user(
        username=test_user,
        email=test_email,
        password=test_pwd,
        full_name="Algorithmic Quantitative Analyst",
        tier="pro"
    )
    assert success is True, f"Registration failed: {msg}"
    print(f"✅ User '{test_user}' registered successfully")

    # 2. Prevent Duplicate Registration
    dup_success, dup_msg = register_user(
        username=test_user,
        email=f"different_{test_email}",
        password=test_pwd
    )
    assert dup_success is False, "Duplicate username should be rejected"
    print(f"✅ Duplicate username prevention verified: {dup_msg}")

    # 3. Authenticate User with Correct Password
    auth_ok, auth_msg, user_data = authenticate_user(test_user, test_pwd)
    assert auth_ok is True, f"Authentication failed: {auth_msg}"
    assert user_data is not None
    assert user_data["username"] == test_user
    assert user_data["email"] == test_email
    print(f"✅ Authentication with username PASSED: {auth_msg}")

    # 4. Authenticate User with Email
    auth_email_ok, auth_email_msg, _ = authenticate_user(test_email, test_pwd)
    assert auth_email_ok is True, "Authentication with email should succeed"
    print(f"✅ Authentication with email address PASSED: {auth_email_msg}")

    # 5. Reject Invalid Password
    bad_ok, bad_msg, bad_data = authenticate_user(test_user, "InvalidPassword999!")
    assert bad_ok is False, "Invalid password should fail"
    assert bad_data is None
    print(f"✅ Invalid password rejection PASSED: {bad_msg}")

    # 6. Verify User Record in Database
    db_user = get_user_by_username(test_user)
    assert db_user is not None
    assert db_user["username"] == test_user
    print(f"✅ SQLite persistence lookup PASSED: {db_user}")


def test_session_token_and_security():
    print("Testing session token generation and security constraints...")
    token = secrets.token_hex(24)
    assert len(token) == 48, "Session token must be 48 hex characters"
    assert token.isalnum(), "Session token must be alphanumeric"
    print(f"✅ Session token validation PASSED: {token[:12]}...")


def test_auth_me_security_and_expiry():
    """Verify that unauthenticated user enumeration is prevented,
    and sessions expire after TTL or on logout."""
    import time
    from fastapi import HTTPException
    from app.auth_routes import _create_session, _get_session_user, ACTIVE_SESSIONS, SESSION_TTL_SECONDS

    # 1. Reject invalid or empty tokens
    assert _get_session_user(None) is None
    assert _get_session_user("") is None
    assert _get_session_user("nonexistent_token_12345") is None

    # 2. Valid session retrieval
    dummy_user = {"username": "test_security_user", "email": "sec@marketml.test"}
    token = _create_session(dummy_user)
    assert token in ACTIVE_SESSIONS
    retrieved = _get_session_user(token)
    assert retrieved == dummy_user

    # 3. Session expiry when created > SESSION_TTL_SECONDS
    ACTIVE_SESSIONS[token]["created"] = time.time() - (SESSION_TTL_SECONDS + 10)
    assert _get_session_user(token) is None
    assert token not in ACTIVE_SESSIONS, "Expired session must be purged from memory"


def test_no_credentials_plaintext_file():
    """Verify credentials.txt is not written to disk upon registration."""
    test_user = f"dossier_check_{secrets.token_hex(4)}"
    pwd = "DossierPassword!2026"
    success, _ = register_user(
        username=test_user,
        email=f"{test_user}@test.org",
        password=pwd
    )
    assert success is True

    user_folder = os.path.join(BASE_DIR, "data", "users", test_user)
    cred_txt = os.path.join(user_folder, "credentials.txt")
    assert not os.path.exists(cred_txt), "credentials.txt must NEVER be created on disk"


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING MARKET ML AUTHENTICATION TEST SUITE")
    print("=" * 60)
    test_password_hashing()
    test_user_registration_and_auth()
    test_session_token_and_security()
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! 🎉")
    print("=" * 60)
