"""
Authentication and User Management Module
Provides secure user registration, password hashing (PBKDF2-HMAC-SHA256),
credential verification, and SQLite user database management.
"""

import hashlib
import os
import re
import secrets
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

# Path to database directory and file
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
    """Initialize database tables and seed default accounts if missing."""
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
                tier TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Check if default demo accounts exist, seed if not
        cursor.execute("SELECT COUNT(*) as count FROM users")
        row = cursor.fetchone()
        if row and row["count"] == 0:
            # Seed default admin and demo user
            admin_hash, admin_salt = hash_password("admin123")
            demo_hash, demo_salt = hash_password("demo123")
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, full_name, tier)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("admin", "admin@marketpulse.io", admin_hash, admin_salt, "System Administrator", "admin"))
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, full_name, tier)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("demo_user", "demo@marketpulse.io", demo_hash, demo_salt, "Demo Trader", "pro"))
            
            conn.commit()


def register_user(
    username: str,
    email: str,
    password: str,
    full_name: str = "",
    tier: str = "free"
) -> Tuple[bool, str]:
    """
    Register a new user in the database.
    Returns (success: bool, message: str).
    """
    init_auth_db()
    
    # Input validation
    username = username.strip()
    email = email.strip().lower()
    full_name = full_name.strip()
    
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long."
    
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username may only contain alphanumeric characters and underscores."
        
    if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return False, "Please enter a valid email address."
        
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."

    if tier not in ("free", "pro", "admin"):
        tier = "free"

    pwd_hash, salt = hash_password(password)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, full_name, tier)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, email, pwd_hash, salt, full_name or username, tier))
            conn.commit()
        return True, "Account created successfully! You can now log in."
    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if "username" in err_msg:
            return False, f"Username '{username}' is already taken. Please choose another."
        elif "email" in err_msg:
            return False, f"Email '{email}' is already registered. Please log in instead."
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
                return False, "Invalid username/email or password.", None

            if not verify_password(password, user["password_hash"], user["salt"]):
                return False, "Invalid username/email or password.", None

            user_data = {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"] or user["username"],
                "tier": user["tier"] or "free",
                "created_at": user["created_at"],
            }
            return True, f"Welcome back, {user_data['full_name']}!", user_data
    except Exception as e:
        return False, f"Authentication error: {e}", None


def get_user_info(username_or_email: str) -> Optional[Dict[str, Any]]:
    """Retrieve non-sensitive user information."""
    init_auth_db()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, full_name, tier, created_at
                FROM users
                WHERE username = ? OR email = ?
            """, (username_or_email.strip(), username_or_email.strip().lower()))
            user = cursor.fetchone()
            if user:
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "full_name": user["full_name"] or user["username"],
                    "tier": user["tier"] or "free",
                    "created_at": user["created_at"],
                }
    except Exception:
        pass
    return None


# Initialize on import
init_auth_db()
