"""
Real-Time Live User Audit & Directory Synchronizer
Connects to the MarketPulse Live Cloud Stream.
Whenever any user from any computer registers, signs in, or moves on the website:
1. Displays the live activity trail in this terminal in real-time.
2. Automatically creates and updates their folder in `data/users/<username>/` with:
   - USER_PROFILE_&_ACTIVITY_REPORT.txt (Dossier)
   - activity_log.csv (Excel Spreadsheet)
   - searched_stocks.txt (Stocks viewed)
   - profile.json (Metadata)
"""

import json
import os
import sys
import time
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

    # Ensure user folder exists on Mac
    ensure_user_directory(username, user_prof if user_prof else None)

    # Format human-readable terminal line
    action_icon = "🔵"
    summary_text = ""

    if action == "USER_REGISTRATION":
        action_icon = "🟢"
        full_name = details.get("full_name") or user_prof.get("full_name") or username
        email = details.get("email") or user_prof.get("email") or "N/A"
        tier = details.get("tier") or user_prof.get("tier") or "PRO"
        summary_text = f"NEW ACCOUNT CREATED -> Name: {full_name} | Email: {email} | Tier: {tier.upper()}"

    elif action == "USER_LOGIN":
        action_icon = "🔐"
        email = details.get("email") or user_prof.get("email") or "N/A"
        summary_text = f"USER LOGGED IN -> Email: {email}"

    elif action == "USER_LOGOUT":
        action_icon = "🚪"
        summary_text = "USER LOGGED OUT"

    elif action == "VIEW_ANALYSIS":
        action_icon = "📈"
        ticker = details.get("ticker", "N/A")
        period = details.get("time_range", "1y")
        summary_text = f"VIEWED STOCK ANALYSIS -> Ticker: {ticker} (Period: {period})"

    elif action == "VIEW_ML_PREDICTIONS":
        action_icon = "🤖"
        ticker = details.get("ticker", "N/A")
        model = details.get("model", "N/A")
        summary_text = f"RAN MACHINE LEARNING PREDICTION -> Ticker: {ticker} | Model: {model}"

    elif action == "VIEW_PORTFOLIO":
        action_icon = "💼"
        portfolio_name = details.get("portfolio", "N/A")
        summary_text = f"ANALYZED PORTFOLIO -> Strategy: {portfolio_name}"

    elif action == "VIEW_COMPARISON":
        action_icon = "⚖️"
        tickers = details.get("tickers", "N/A")
        summary_text = f"COMPARED STOCKS -> {tickers}"

    else:
        action_icon = "⚡"
        details_str = ", ".join(f"{k}: {v}" for k, v in details.items())
        summary_text = f"{action} -> {details_str}"

    # Print live trail in terminal
    local_time = time.strftime("%H:%M:%S")
    print(f"[{local_time}] {action_icon} @{username:<14} | {summary_text}")

    # Write directly to local user directory on Mac
    track_activity(action, username, details, skip_broadcast=True)


def main():
    print("\n" + "=" * 80)
    print(" 📡 MARKETPULSE REAL-TIME LIVE AUDIT STREAM & BACKEND SYNCHRONIZER")
    print("=" * 80)
    print(f" • Local Storage Directory:  {USERS_DIR}")
    print(f" • Live Activity Feed:       🟢 CONNECTED & LISTENING (Sub-second latency)")
    print(" • Features:")
    print("   1. Live activity trail for every user across any computer / phone.")
    print("   2. Automatic creation & update of data/users/<username>/ in Finder.")
    print("=" * 80)
    print(" Waiting for live user activities on website (Press Ctrl+C to stop)...\n")

    try:
        listen_live_stream(handle_incoming_cloud_event)
    except KeyboardInterrupt:
        print("\n Stream listener stopped.")


if __name__ == "__main__":
    main()
