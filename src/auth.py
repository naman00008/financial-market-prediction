"""
Authentication and User Management Module
Provides secure user registration, password hashing (PBKDF2-HMAC-SHA256),
credential verification, SQLite user database management, and automatic
per-user filesystem directory initialization.
"""

import hashlib
import os
import re
import secrets
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from src.tracker import ensure_user_directory, track_activity

# Database storage path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "users.db")


def get_db_connection() -> sqlite3.Connection:
    """Ensure data directory exists and return SQLite connection."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a plaintext password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Returns (hex_hash, salt).
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    )
    return key.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password matches the stored hash."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


def init_auth_db() -> None:
    """Initialize database tables and sync all existing user directories."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                tier TEXT DEFAULT 'pro',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Automatically ensure all registered users have provisioned directories and reports
        try:
            from src.tracker import ensure_user_directory, update_user_human_readable_report
            cursor.execute("SELECT id, username, email, full_name, tier, created_at FROM users")
            existing_users = cursor.fetchall()
            for u in existing_users:
                u_dict = {
                    "id": u["id"],
                    "username": u["username"],
                    "email": u["email"],
                    "full_name": u["full_name"],
                    "tier": u["tier"],
                    "created_at": u["created_at"]
                }
                ensure_user_directory(u["username"], u_dict)
                update_user_human_readable_report(u["username"])
        except Exception:
            pass


def register_user(
    username: str,
    email: str,
    password: str,
    full_name: str = "",
    tier: str = "pro"
) -> Tuple[bool, str]:
    """
    Register a new user in the SQLite database and create their dedicated folder.
    Returns (success: bool, message: str).
    """
    init_auth_db()
    
    username = username.strip()
    email = email.strip().lower()
    full_name = full_name.strip()
    
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long."
    
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username may only contain letters, numbers, and underscores."
        
    if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return False, "Please provide a valid corporate or personal email address."
        
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."

    pwd_hash, salt = hash_password(password)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, full_name, tier)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, email, pwd_hash, salt, full_name or username, tier))
            conn.commit()
            user_id = cursor.lastrowid

        user_info = {
            "id": user_id,
            "username": username,
            "email": email,
            "full_name": full_name or username,
            "tier": tier,
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        }

        # 1. Create dedicated user folder: data/users/<username>/
        ensure_user_directory(username, user_info)

        # 2. Record registration audit event
        track_activity(
            action="USER_REGISTRATION",
            username=username,
            details={"email": email, "full_name": full_name, "tier": tier}
        )

        return True, "Account created successfully! You are now authorized."
    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if "username" in err_msg:
            return False, f"Username '{username}' is already registered. Please choose another."
        elif "email" in err_msg:
            return False, f"Email '{email}' is already registered. Please sign in."
        return False, "An account with these details already exists."
    except Exception as e:
        return False, f"Database error: {e}"


def authenticate_user(username_or_email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticate user by username or email and password.
    Returns (success: bool, message: str, user_dict: Optional[dict]).
    """
    init_auth_db()
    
    identifier = username_or_email.strip()
    if not identifier or not password:
        return False, "Please provide both username/email and password.", None

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, password_hash, salt, full_name, tier, created_at
                FROM users
                WHERE username = ? OR email = ?
            """, (identifier, identifier.lower()))
            
            user = cursor.fetchone()
            if not user:
                return False, "Invalid credentials. Please verify username and password.", None

            if not verify_password(password, user["password_hash"], user["salt"]):
                return False, "Invalid credentials. Please verify username and password.", None

            user_data = {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"] or user["username"],
                "tier": user["tier"] or "pro",
                "created_at": user["created_at"],
            }

            # Ensure user directory structure exists
            ensure_user_directory(user["username"], user_data)

            # Record login audit event
            track_activity(
                action="USER_LOGIN",
                username=user["username"],
                details={"identifier_used": identifier}
            )

            return True, f"Welcome back, {user_data['full_name']}.", user_data
    except Exception as e:
        return False, f"Authentication error: {e}", None


# Initialize database table on module load
init_auth_db()
