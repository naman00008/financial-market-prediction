"""
Authentication and User Management Module
Provides secure user registration, password hashing (PBKDF2-HMAC-SHA256),
credential verification, SQLite user database management, and automatic
per-user filesystem directory initialization with credentials & activity dossiers.
"""

import hashlib
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from src.tracker import ensure_user_directory, track_activity, update_user_human_readable_report, USERS_DIR

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


def save_user_credentials_record(username: str, user_dict: Dict[str, Any], pwd_hash: str, salt: str) -> None:
    """
    Save complete credential and authentication records directly inside the user's folder:
    data/users/<username>/credentials.txt and credentials.json
    """
    safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
    user_folder = os.path.join(USERS_DIR, safe_username)
    os.makedirs(user_folder, exist_ok=True)

    # 1. Structured JSON credentials record
    cred_json_path = os.path.join(user_folder, "credentials.json")
    cred_data = {
        "username": safe_username,
        "full_name": user_dict.get("full_name", safe_username),
        "email": user_dict.get("email", ""),
        "tier": user_dict.get("tier", "pro"),
        "registered_at": user_dict.get("created_at", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")),
        "password_hash": pwd_hash,
        "salt": salt,
        "hashing_algorithm": "PBKDF2-HMAC-SHA256",
        "iterations": 100000
    }
    try:
        with open(cred_json_path, "w", encoding="utf-8") as f:
            json.dump(cred_data, f, indent=2)
    except Exception:
        pass

    # 2. Institutional Human-Readable Plaintext Credentials Dossier
    cred_txt_path = os.path.join(user_folder, "credentials.txt")
    cred_lines = [
        "=" * 80,
        f" USER CREDENTIALS & SECURITY RECORD: @{safe_username}",
        "=" * 80,
        f" Username:          @{safe_username}",
        f" Full Name:         {cred_data['full_name']}",
        f" Email Address:     {cred_data['email']}",
        f" Membership Tier:   {str(cred_data['tier']).upper()}",
        f" Registration Date: {cred_data['registered_at']}",
        f" Storage Location:  data/users/{safe_username}/",
        f" Security Method:   PBKDF2-HMAC-SHA256 (100,000 Rounds)",
        f" Cryptographic Salt: {salt}",
        f" Password Hash:     {pwd_hash}",
        "=" * 80,
        " This record is automatically generated and synchronized on every login/update.",
        "=" * 80,
    ]
    try:
        with open(cred_txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(cred_lines) + "\n")
    except Exception:
        pass


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

        # Automatically ensure all registered users have provisioned directories, credentials, and reports
        try:
            cursor.execute("SELECT id, username, email, password_hash, salt, full_name, tier, created_at FROM users")
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
                save_user_credentials_record(u["username"], u_dict, u["password_hash"], u["salt"])
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
    Register a new user in the SQLite database and create their dedicated folder with credentials.
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

        # 2. Store credentials file in user folder
        save_user_credentials_record(username, user_info, pwd_hash, salt)

        # 3. Record registration audit event
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

            # Ensure credentials files are saved in folder
            save_user_credentials_record(user["username"], user_data, user["password_hash"], user["salt"])

            # Record login audit event
            track_activity(
                action="USER_LOGIN",
                username=user["username"],
                details={"identifier_used": identifier, "email": user["email"], "tier": user["tier"]}
            )

            return True, f"Welcome back, {user_data['full_name']}.", user_data
    except Exception as e:
        return False, f"Authentication error: {e}", None


# Initialize database table and existing user directories on module load
init_auth_db()
