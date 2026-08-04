"""
MarketPulse Institutional Live User Audit & Synchronization Engine
Connects to the cloud telemetry stream.
Captures real-time transactions, logins, model training runs, and updates
per-user audit records in data/users/<username>/
"""

import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")

from src.cloud_stream import listen_live_stream
from src.tracker import (
    ensure_user_directory,
    track_activity,
    update_user_human_readable_report,
    USERS_DIR
)

seen_events = set()


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

    if username and username != "guest":
        ensure_user_directory(username, user_prof if user_prof else None)

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
        summary_text = f"SESSION CLOSED | Dossier finalized in data/users/{username}/"

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

    elif action in ("VIEW_PORTFOLIO", "OPTIMIZE_PORTFOLIO"):
        category_tag = "[PORTFOLIO]"
        portfolio_name = details.get("portfolio", details.get("strategy", "Custom"))
        tickers = details.get("tickers", "")
        tickers_str = f" | Assets: {tickers}" if tickers else ""
        summary_text = f"PORTFOLIO MANAGEMENT | Strategy: {portfolio_name}{tickers_str}"

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
    print(f"[{local_time}] {category_tag:<11} [USER: {username:<12}] {summary_text}", flush=True)

    if username and username != "guest":
        track_activity(action, username, details, skip_broadcast=True)


def main():
    print("\n" + "=" * 88, flush=True)
    print(" MARKETPULSE INSTITUTIONAL AUDIT & SYNCHRONIZATION ENGINE [v3.4]", flush=True)
    print("=" * 88, flush=True)
    print(f" Storage Directory:  {USERS_DIR}", flush=True)
    print(" Telemetry Stream:   ONLINE [Sub-millisecond socket listener]", flush=True)
    print(" Audit Mode:         Continuous Multi-User Synchronization", flush=True)
    print("=" * 88, flush=True)
    print(" Listening for live user events (Press Ctrl+C to terminate)...\n", flush=True)

    try:
        listen_live_stream(handle_incoming_cloud_event)
    except KeyboardInterrupt:
        print("\n Audit listener terminated.", flush=True)


if __name__ == "__main__":
    main()
