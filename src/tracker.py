"""
User Activity and Audit Logging Engine
Creates dedicated per-user filesystem directories (data/users/<username>/)
and logs every user action, tab view, stock search, model run, and interaction.
"""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Base directory paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_DIR = os.path.join(DATA_DIR, "users")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
GLOBAL_LOG_PATH = os.path.join(LOGS_DIR, "activity_stream.jsonl")


def init_storage_directories() -> None:
    """Ensure data directories for users and logs exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(USERS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)


def ensure_user_directory(username: str, user_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a dedicated directory structure for a specific user:
    data/users/<username>/
        ├── profile.json
        ├── activity_logs/
        │   └── activity.jsonl
        ├── portfolios/
        └── saved_predictions/
    """
    init_storage_directories()
    safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
    if not safe_username:
        safe_username = "guest"

    user_folder = os.path.join(USERS_DIR, safe_username)
    activity_folder = os.path.join(user_folder, "activity_logs")
    portfolio_folder = os.path.join(user_folder, "portfolios")
    predictions_folder = os.path.join(user_folder, "saved_predictions")

    os.makedirs(user_folder, exist_ok=True)
    os.makedirs(activity_folder, exist_ok=True)
    os.makedirs(portfolio_folder, exist_ok=True)
    os.makedirs(predictions_folder, exist_ok=True)

    profile_path = os.path.join(user_folder, "profile.json")
    if not os.path.exists(profile_path) and user_data:
        profile_info = {
            "id": user_data.get("id"),
            "username": safe_username,
            "email": user_data.get("email", ""),
            "full_name": user_data.get("full_name", safe_username),
            "tier": user_data.get("tier", "free"),
            "registered_at": user_data.get("created_at", datetime.utcnow().isoformat()),
            "last_active": datetime.utcnow().isoformat(),
            "total_actions_recorded": 0
        }
        try:
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(profile_info, f, indent=2)
        except Exception:
            pass

    return user_folder


def track_activity(
    action: str,
    username: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> None:
    """
    Record an audit log entry for any user interaction in real time.
    Writes to:
    1. The user's private activity stream: data/users/<username>/activity_logs/activity.jsonl
    2. The global backend activity audit log: data/logs/activity_stream.jsonl
    """
    init_storage_directories()
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    epoch_time = time.time()
    
    user_label = username.strip().lower() if username else "guest"
    
    log_entry = {
        "timestamp": timestamp,
        "epoch": epoch_time,
        "username": user_label,
        "action": action,
        "details": details or {},
        "session_id": session_id or ""
    }

    log_line = json.dumps(log_entry) + "\n"

    # 1. Write to global log
    try:
        with open(GLOBAL_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass

    # 2. Write to user's individual directory if a registered user
    if username and username != "guest":
        try:
            user_folder = ensure_user_directory(username)
            user_log_path = os.path.join(user_folder, "activity_logs", "activity.jsonl")
            with open(user_log_path, "a", encoding="utf-8") as f:
                f.write(log_line)

            # Update profile last active timestamp
            profile_path = os.path.join(user_folder, "profile.json")
            if os.path.exists(profile_path):
                with open(profile_path, "r", encoding="utf-8") as f:
                    prof = json.load(f)
                prof["last_active"] = timestamp
                prof["total_actions_recorded"] = prof.get("total_actions_recorded", 0) + 1
                with open(profile_path, "w", encoding="utf-8") as f:
                    json.dump(prof, f, indent=2)
        except Exception:
            pass


def get_user_activity_history(username: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve chronological activity log for a specific user."""
    safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
    log_path = os.path.join(USERS_DIR, safe_username, "activity_logs", "activity.jsonl")
    
    if not os.path.exists(log_path):
        return []

    entries = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line.strip()))
    except Exception:
        pass

    return entries[-limit:][::-1]


def get_all_registered_user_folders() -> List[Dict[str, Any]]:
    """List all user folders created in the backend with their profile metadata."""
    init_storage_directories()
    if not os.path.exists(USERS_DIR):
        return []

    users = []
    for uname in os.listdir(USERS_DIR):
        user_path = os.path.join(USERS_DIR, uname)
        if os.path.isdir(user_path):
            profile_path = os.path.join(user_path, "profile.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, "r", encoding="utf-8") as f:
                        users.append(json.load(f))
                except Exception:
                    users.append({"username": uname, "status": "active"})
            else:
                users.append({"username": uname, "status": "active"})
    return users


# Initialize on import
init_storage_directories()
