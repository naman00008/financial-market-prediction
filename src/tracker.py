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
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
GLOBAL_LOG_PATH = os.path.join(LOGS_DIR, "activity_stream.jsonl")

try:
    from src.cloud_stream import publish_cloud_event
except Exception:
    try:
        from cloud_stream import publish_cloud_event
    except Exception:
        def publish_cloud_event(*args, **kwargs):
            pass


def init_storage_directories() -> None:
    """Ensure data directories for users and logs exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(USERS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)


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
    if not safe_username or safe_username == "guest":
        return USERS_DIR

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

    # Ensure searched_stocks.txt exists
    stocks_path = os.path.join(user_folder, "searched_stocks.txt")
    if not os.path.exists(stocks_path):
        try:
            with open(stocks_path, "w", encoding="utf-8") as f:
                f.write(f"# Stock Search & View History for @{safe_username}\n")
        except Exception:
            pass

    # Ensure initial report exists
    report_path = os.path.join(user_folder, "USER_PROFILE_&_ACTIVITY_REPORT.txt")
    if not os.path.exists(report_path):
        update_user_human_readable_report(safe_username)

    return user_folder


def save_user_prediction(
    username: str,
    ticker: str,
    model_name: str,
    metrics: Dict[str, Any],
    predictions_summary: Optional[Dict[str, Any]] = None
) -> str:
    """Save machine learning model results directly to data/users/<username>/saved_predictions/."""
    safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
    if not safe_username or safe_username == "guest":
        return ""
    
    user_folder = ensure_user_directory(safe_username)
    pred_folder = os.path.join(user_folder, "saved_predictions")
    os.makedirs(pred_folder, exist_ok=True)
    
    ts_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    clean_model = model_name.replace(" ", "_").replace("/", "_")
    filename = f"{ticker}_{clean_model}_{ts_str}.json"
    filepath = os.path.join(pred_folder, filename)
    
    payload = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "username": safe_username,
        "ticker": ticker,
        "model_name": model_name,
        "metrics": metrics,
        "predictions_summary": predictions_summary or {}
    }
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass
    
    return filepath


def save_user_portfolio(
    username: str,
    strategy_name: str,
    tickers: List[str],
    weights: Dict[str, float],
    metrics: Dict[str, Any]
) -> str:
    """Save optimized portfolio allocations directly to data/users/<username>/portfolios/."""
    safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
    if not safe_username or safe_username == "guest":
        return ""
    
    user_folder = ensure_user_directory(safe_username)
    port_folder = os.path.join(user_folder, "portfolios")
    os.makedirs(port_folder, exist_ok=True)
    
    ts_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    clean_strategy = strategy_name.replace(" ", "_").replace("/", "_")
    filename = f"{clean_strategy}_{ts_str}.json"
    filepath = os.path.join(port_folder, filename)
    
    payload = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "username": safe_username,
        "strategy_name": strategy_name,
        "tickers": tickers,
        "weights": weights,
        "metrics": metrics
    }
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass
    
    return filepath


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
        f" MARKETPULSE USER AUDIT DOSSIER: @{safe_username}",
        "=" * 80,
        f" Full Name:         {prof.get('full_name', 'N/A')}",
        f" Username:          @{safe_username}",
        f" Email Address:     {prof.get('email', 'N/A')}",
        f" Membership Tier:   {str(prof.get('tier', 'PRO')).upper()}",
        f" Registered Date:   {prof.get('registered_at', 'N/A')}",
        f" Last Active Time:  {prof.get('last_active', 'N/A')}",
        f" Total Activities:  {len(events)} recorded transactions",
        "=" * 80,
        "\n CHRONOLOGICAL AUDIT TRAIL (Most Recent First):",
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
    session_id: Optional[str] = None,
    skip_broadcast: bool = False
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
            safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
            user_folder = ensure_user_directory(safe_username)
            
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
            update_user_human_readable_report(safe_username)

            # Publish updated live static sync files
            publish_static_sync_payload()

        except Exception:
            pass

    # 3. Broadcast to live audit stream
    if not skip_broadcast:
        try:
            prof_data = {}
            if username and username != "guest":
                safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
                profile_path = os.path.join(USERS_DIR, safe_username, "profile.json")
                if os.path.exists(profile_path):
                    with open(profile_path, "r", encoding="utf-8") as f:
                        prof_data = json.load(f)
            publish_cloud_event(action, user_label, det, prof_data)
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


def export_all_backend_data() -> Dict[str, Any]:
    """Package all backend user directories, logs, and database entries for synchronization."""
    init_storage_directories()
    
    users_data = {}
    if os.path.exists(USERS_DIR):
        for uname in sorted(os.listdir(USERS_DIR)):
            user_dir = os.path.join(USERS_DIR, uname)
            if not os.path.isdir(user_dir):
                continue
            
            user_pack = {}
            for fname in ["profile.json", "USER_PROFILE_&_ACTIVITY_REPORT.txt", "activity_log.csv", "searched_stocks.txt"]:
                fpath = os.path.join(user_dir, fname)
                if os.path.exists(fpath):
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            user_pack[fname] = f.read()
                    except Exception:
                        pass
            
            act_jsonl = os.path.join(user_dir, "activity_logs", "activity.jsonl")
            if os.path.exists(act_jsonl):
                try:
                    with open(act_jsonl, "r", encoding="utf-8") as f:
                        user_pack["activity.jsonl"] = f.read()
                except Exception:
                    pass
            
            users_data[uname] = user_pack

    global_log_content = ""
    if os.path.exists(GLOBAL_LOG_PATH):
        try:
            with open(GLOBAL_LOG_PATH, "r", encoding="utf-8") as f:
                global_log_content = f.read()
        except Exception:
            pass

    return {
        "status": "success",
        "exported_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "users": users_data,
        "global_log": global_log_content
    }


def apply_backend_data_bundle(bundle: Dict[str, Any]) -> int:
    """Save imported cloud user data bundle directly into local filesystem."""
    init_storage_directories()
    users_dict = bundle.get("users", {})
    count = 0
    
    for uname, files in users_dict.items():
        if not uname:
            continue
        user_folder = ensure_user_directory(uname)
        
        for fname, content in files.items():
            if fname == "activity.jsonl":
                target = os.path.join(user_folder, "activity_logs", "activity.jsonl")
            else:
                target = os.path.join(user_folder, fname)
            
            try:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                pass
        count += 1

    if bundle.get("global_log"):
        try:
            with open(GLOBAL_LOG_PATH, "w", encoding="utf-8") as f:
                f.write(bundle["global_log"])
        except Exception:
            pass

    return count


def create_users_zip_archive() -> bytes:
    """Create a in-memory ZIP archive of the entire data/users/ and data/logs/ directories."""
    import io
    import zipfile
    init_storage_directories()
    
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add all user folders
        if os.path.exists(USERS_DIR):
            for root, _, files in os.walk(USERS_DIR):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, DATA_DIR)
                    zf.write(full_path, arcname=os.path.join("data", rel_path))
        
        # Add logs
        if os.path.exists(LOGS_DIR):
            for root, _, files in os.walk(LOGS_DIR):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, DATA_DIR)
                    zf.write(full_path, arcname=os.path.join("data", rel_path))

    buf.seek(0)
    return buf.getvalue()


def publish_static_sync_payload() -> None:
    """Publish current state of all user directories to app/static/ for seamless cloud-to-local sync."""
    try:
        init_storage_directories()
        payload = export_all_backend_data()
        json_target = os.path.join(STATIC_DIR, "users_sync.json")
        with open(json_target, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        zip_target = os.path.join(STATIC_DIR, "users_cloud_data.zip")
        zip_bytes = create_users_zip_archive()
        with open(zip_target, "wb") as f:
            f.write(zip_bytes)
    except Exception:
        pass


# Initialize on import
init_storage_directories()
publish_static_sync_payload()
