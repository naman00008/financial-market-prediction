"""
User Activity and Audit Logging Engine
Creates dedicated per-user filesystem directories (data/users/<username>/)
and generates human-readable Text Reports, Excel CSV spreadsheets, and
JSON logs inside each user's folder for instant viewing without terminal commands.
"""

import csv
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
        ├── USER_PROFILE_&_ACTIVITY_REPORT.txt  (Human-readable summary for TextEdit/QuickLook)
        ├── activity_log.csv                    (Spreadsheet for Excel/Numbers)
        ├── searched_stocks.txt                 (List of stocks viewed)
        ├── profile.json                        (Metadata)
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
            "tier": user_data.get("tier", "pro"),
            "registered_at": user_data.get("created_at", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")),
            "last_active": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_actions_recorded": 0
        }
        try:
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(profile_info, f, indent=2)
        except Exception:
            pass

    # Ensure CSV file has headers
    csv_path = os.path.join(user_folder, "activity_log.csv")
    if not os.path.exists(csv_path):
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp (UTC)", "Action Type", "Stock Ticker", "Details / Parameters"])
        except Exception:
            pass

    return user_folder


def update_user_human_readable_report(username: str) -> None:
    """Regenerate the human-readable plain text report inside the user's folder."""
    safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
    user_folder = os.path.join(USERS_DIR, safe_username)
    if not os.path.exists(user_folder):
        return

    profile_path = os.path.join(user_folder, "profile.json")
    prof = {}
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                prof = json.load(f)
        except Exception:
            pass

    log_path = os.path.join(user_folder, "activity_logs", "activity.jsonl")
    events = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line.strip()))
        except Exception:
            pass

    report_lines = [
        "=" * 80,
        f" USER DOSSIER & ACTIVITY REPORT: @{safe_username}",
        "=" * 80,
        f" • Full Name:         {prof.get('full_name', 'N/A')}",
        f" • Username:          @{safe_username}",
        f" • Email Address:     {prof.get('email', 'N/A')}",
        f" • Membership Tier:   {str(prof.get('tier', 'PRO')).upper()}",
        f" • Registered Date:   {prof.get('registered_at', 'N/A')}",
        f" • Last Active Time:  {prof.get('last_active', 'N/A')}",
        f" • Total Activities:  {len(events)} logged movements",
        "=" * 80,
        "\n CHRONOLOGICAL USER ACTIVITY TIMELINE (Most Recent First):",
        "-" * 80,
    ]

    if not events:
        report_lines.append(" [No user actions recorded yet]")
    else:
        for idx, ev in enumerate(events[::-1], 1):
            ts = ev.get("timestamp", "N/A")
            act = ev.get("action", "UNKNOWN")
            details = ev.get("details", {})
            detail_str = ", ".join(f"{k}: {v}" for k, v in details.items()) if details else "None"
            report_lines.append(f" {idx:02d}. [{ts}]  {act:<24}  |  {detail_str}")

    report_lines.append("\n" + "=" * 80 + "\n")

    report_path = os.path.join(user_folder, "USER_PROFILE_&_ACTIVITY_REPORT.txt")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
    except Exception:
        pass


def track_activity(
    action: str,
    username: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> None:
    """
    Record an audit log entry for any user interaction in real time.
    Writes directly to:
    1. data/users/<username>/USER_PROFILE_&_ACTIVITY_REPORT.txt (Human-readable text)
    2. data/users/<username>/activity_log.csv (Excel spreadsheet)
    3. data/users/<username>/activity_logs/activity.jsonl (Raw JSONL)
    4. data/users/<username>/searched_stocks.txt (Ticker summary)
    5. data/logs/activity_stream.jsonl (Global live stream)
    """
    init_storage_directories()
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    epoch_time = time.time()
    user_label = username.strip().lower() if username else "guest"
    det = details or {}
    
    log_entry = {
        "timestamp": timestamp,
        "epoch": epoch_time,
        "username": user_label,
        "action": action,
        "details": det,
        "session_id": session_id or ""
    }

    log_line = json.dumps(log_entry) + "\n"

    # 1. Global stream
    try:
        with open(GLOBAL_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass

    # 2. User-specific directory records
    if username and username != "guest":
        try:
            user_folder = ensure_user_directory(username)
            
            # JSONL Log
            user_log_path = os.path.join(user_folder, "activity_logs", "activity.jsonl")
            with open(user_log_path, "a", encoding="utf-8") as f:
                f.write(log_line)

            # CSV Spreadsheet
            csv_path = os.path.join(user_folder, "activity_log.csv")
            ticker_val = det.get("ticker") or det.get("news_ticker") or det.get("searched_ticker") or "N/A"
            detail_summary = "; ".join(f"{k}={v}" for k, v in det.items())
            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, action, ticker_val, detail_summary])

            # Searched Stocks Tracker
            if "ticker" in det or "news_ticker" in det:
                t = det.get("ticker") or det.get("news_ticker")
                if t and t != "All":
                    stocks_file = os.path.join(user_folder, "searched_stocks.txt")
                    with open(stocks_file, "a", encoding="utf-8") as f:
                        f.write(f"[{timestamp}] {t}\n")

            # Update profile metadata
            profile_path = os.path.join(user_folder, "profile.json")
            if os.path.exists(profile_path):
                with open(profile_path, "r", encoding="utf-8") as f:
                    prof = json.load(f)
                prof["last_active"] = timestamp
                prof["total_actions_recorded"] = prof.get("total_actions_recorded", 0) + 1
                with open(profile_path, "w", encoding="utf-8") as f:
                    json.dump(prof, f, indent=2)

            # Update Human-Readable Plain Text Report
            update_user_human_readable_report(username)

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
    for uname in sorted(os.listdir(USERS_DIR)):
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
