"""
MarketPulse Institutional Live User Audit & Synchronization Engine
Connects to the cloud telemetry stream.
Captures real-time transactions, logins, model training runs, and updates
per-user audit records in data/users/<username>/ and SQLite database data/users.db.
"""

import json
import os
import sqlite3
import sys
import time
import warnings

warnings.filterwarnings("ignore")

import requests
from src.auth import (
    get_db_connection,
    save_user_credentials_record,
    sync_db_and_folders,
    hash_password,
    DB_PATH
)
from src.cloud_stream import listen_live_stream
from src.tracker import (
    apply_backend_data_bundle,
    ensure_user_directory,
    save_user_portfolio,
    save_user_prediction,
    track_activity,
    update_user_human_readable_report,
    USERS_DIR
)

seen_events = set()


def sync_cloud_snapshot() -> None:
    """Fetch complete cloud database and filesystem snapshot from Render on startup."""
    cloud_endpoints = [
        "https://financial-market-prediction.onrender.com/api/sync",
        "https://financial-market-prediction.onrender.com/app/static/live_users_sync.json"
    ]
    for url in cloud_endpoints:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and r.text.strip():
                data = r.json()
                count = apply_backend_data_bundle(data)
                if count > 0:
                    print(f" [INIT] Synced {count} user profile(s) and database records from cloud.", flush=True)
                break
        except Exception:
            pass


def handle_incoming_cloud_event(event: dict) -> None:
    event_id = f"{event.get('epoch')}_{event.get('username')}_{event.get('action')}"
    if event_id in seen_events:
        return
    seen_events.add(event_id)

    username = event.get("username", "guest")
    action = event.get("action", "UNKNOWN")
    timestamp = event.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S UTC"))
    details = event.get("details", {})
    user_prof = event.get("user_profile", {})

    safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()

    if safe_username and safe_username != "guest":
        user_info = {
            "username": safe_username,
            "full_name": details.get("full_name") or user_prof.get("full_name") or safe_username,
            "email": details.get("email") or user_prof.get("email") or f"{safe_username}@marketpulse.io",
            "tier": details.get("tier") or user_prof.get("tier") or "pro",
            "created_at": details.get("created_at") or user_prof.get("registered_at") or timestamp
        }

        # 1. Provision user filesystem directory
        ensure_user_directory(safe_username, user_info)

        # 2. Extract or generate password hash and salt
        pwd_hash = details.get("password_hash") or user_prof.get("password_hash")
        salt = details.get("salt") or user_prof.get("salt")
        if not pwd_hash or not salt:
            pwd_hash, salt = hash_password("MarketPulse123!")

        # 3. Synchronize with local SQLite database data/users.db
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, salt, full_name, tier, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        email=excluded.email,
                        full_name=excluded.full_name,
                        tier=excluded.tier,
                        password_hash=CASE WHEN excluded.password_hash != '' THEN excluded.password_hash ELSE users.password_hash END,
                        salt=CASE WHEN excluded.salt != '' THEN excluded.salt ELSE users.salt END
                """, (
                    safe_username,
                    user_info["email"],
                    pwd_hash,
                    salt,
                    user_info["full_name"],
                    user_info["tier"],
                    user_info["created_at"]
                ))
                conn.commit()
        except Exception:
            pass

        # 4. Save credentials files in user folder
        save_user_credentials_record(safe_username, user_info, pwd_hash, salt)

    category_tag = "[AUDIT]"
    summary_text = ""

    if action == "USER_REGISTRATION":
        category_tag = "[REGISTER]"
        full_name = details.get("full_name") or user_prof.get("full_name") or username
        email = details.get("email") or user_prof.get("email") or "N/A"
        tier = details.get("tier") or user_prof.get("tier") or "PRO"
        summary_text = f"NEW ACCOUNT CREATED | Name: {full_name} | Email: {email} | Tier: {tier.upper()}"

    elif action == "USER_LOGIN":
        category_tag = "[AUTH]"
        email = details.get("email") or user_prof.get("email") or "N/A"
        tier = details.get("tier") or user_prof.get("tier") or "PRO"
        summary_text = f"USER AUTHENTICATED | Email: {email} | Tier: {tier.upper()}"

    elif action == "USER_LOGOUT":
        category_tag = "[LOGOUT]"
        summary_text = f"SESSION CLOSED | Dossier finalized in data/users/{safe_username}/"

    elif action in ("VIEW_ANALYSIS", "VIEW_STOCK_ANALYSIS", "SELECT_STOCK"):
        category_tag = "[MARKET]"
        ticker = details.get("ticker", "N/A")
        period = details.get("time_range", "1y")
        summary_text = f"STOCK ANALYSIS | Ticker: {ticker} | Period: {period}"

    elif action in ("TRAIN_ML_MODELS", "VIEW_ML_PREDICTIONS", "RUN_PREDICTION"):
        category_tag = "[ML-MODEL]"
        ticker = details.get("ticker", "N/A")
        best_model = details.get("best_model", details.get("model", "Regression"))
        rmse = details.get("rmse", details.get("best_rmse", ""))
        rmse_str = f" | RMSE: {rmse}" if rmse else ""
        acc = details.get("directional_accuracy", "")
        acc_str = f" | Accuracy: {acc}" if acc else ""
        summary_text = f"ML MODEL TRAINED | Ticker: {ticker} | Best: {best_model}{rmse_str}{acc_str}"

        # Persist prediction in user folder
        if safe_username and safe_username != "guest":
            save_user_prediction(
                username=safe_username,
                ticker=ticker,
                model_name=best_model,
                metrics={"rmse": rmse, "directional_accuracy": acc}
            )

    elif action in ("VIEW_PORTFOLIO", "OPTIMIZE_PORTFOLIO"):
        category_tag = "[PORTFOLIO]"
        portfolio_name = details.get("portfolio", details.get("strategy", "Custom"))
        tickers = details.get("tickers", "")
        tickers_str = f" | Assets: {tickers}" if tickers else ""
        summary_text = f"PORTFOLIO MANAGEMENT | Strategy: {portfolio_name}{tickers_str}"

        # Persist portfolio in user folder
        if safe_username and safe_username != "guest":
            save_user_portfolio(
                username=safe_username,
                strategy_name=portfolio_name,
                tickers=tickers if isinstance(tickers, list) else [str(tickers)],
                weights=details.get("weights", {}),
                metrics=details.get("metrics", {})
            )

    elif action == "SESSION_STARTED":
        category_tag = "[SESSION]"
        tier = details.get("tier", "PRO").upper()
        summary_text = f"SESSION ACTIVE | Tier: {tier} Member"

    elif action in ("VIEW_NEWS_SENTIMENT", "SEARCH_NEWS"):
        category_tag = "[NEWS]"
        news_ticker = details.get("news_ticker", details.get("ticker", "All"))
        summary_text = f"NEWS & SENTIMENT | Ticker: {news_ticker}"

    elif action in ("VIEW_COMPARISON", "VIEW_STOCK_COMPARISON", "COMPARE_STOCKS"):
        category_tag = "[COMPARE]"
        tickers = details.get("tickers", "Multi-Stock")
        summary_text = f"STOCK COMPARISON | Assets: {tickers}"

    else:
        category_tag = "[ACTION]"
        details_str = " | ".join(f"{k}: {v}" for k, v in details.items())
        summary_text = f"{action} | {details_str}"

    local_time = time.strftime("%H:%M:%S")
    print(f"[{local_time}] {category_tag:<11} [USER: {safe_username:<12}] {summary_text}", flush=True)

    if safe_username and safe_username != "guest":
        track_activity(action, safe_username, details, skip_broadcast=True)


def main():
    print("\n" + "=" * 88, flush=True)
    print(" MARKETPULSE INSTITUTIONAL AUDIT & DATABASE SYNCHRONIZATION ENGINE [v3.5]", flush=True)
    print("=" * 88, flush=True)
    print(f" SQLite Database:    {DB_PATH}", flush=True)
    print(f" Storage Directory:  {USERS_DIR}", flush=True)
    print(" Telemetry Stream:   ONLINE [Sub-millisecond socket listener]", flush=True)
    print(" Audit Mode:         Continuous Multi-User & Database Synchronization", flush=True)
    print("=" * 88, flush=True)

    # 1. Sync local database with local user folders
    sync_db_and_folders()

    # 2. Check cloud server for existing accounts
    sync_cloud_snapshot()

    print(" Listening for live user events & syncing database (Press Ctrl+C to terminate)...\n", flush=True)

    try:
        listen_live_stream(handle_incoming_cloud_event)
    except KeyboardInterrupt:
        print("\n Audit listener terminated.", flush=True)


if __name__ == "__main__":
    main()
