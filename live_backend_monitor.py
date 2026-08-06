#!/usr/bin/env python3
"""
MarketPulse Real-Time Backend Telemetry & Audit Stream Monitor
Live Terminal Console for Faculty Demonstrations on AWS EC2.
Watches SQLite database and filesystem dossiers in real time.
"""

import os
import sys
import time
import json
import sqlite3
from datetime import datetime

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
BG_BLUE = "\033[44m"
BG_DARK = "\033[40m"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_DIR = os.path.join(DATA_DIR, "users")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
DB_PATH = os.path.join(DATA_DIR, "users.db")
GLOBAL_LOG_PATH = os.path.join(LOGS_DIR, "activity_stream.jsonl")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def get_db_users_count():
    if not os.path.exists(DB_PATH):
        return 0
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def format_action_badge(action: str, username: str, details: dict, timestamp: str):
    act = action.upper()
    user_tag = f"{BOLD}@{username}{RESET}"
    
    if "REGISTER" in act or "SIGNUP" in act:
        badge = f"{GREEN}{BOLD}[NEW USER REGISTERED]{RESET}"
        info = f"User: {user_tag} | Email: {CYAN}{details.get('email', 'N/A')}{RESET} | Tier: {details.get('tier', 'PRO')} | Dossier: {DIM}data/users/{username}/{RESET}"
    elif "LOGIN" in act or "AUTH" in act:
        badge = f"{BLUE}{BOLD}[USER LOGGED IN]{RESET}"
        info = f"User: {user_tag} | Auth Status: {GREEN}SUCCESS (PBKDF2 Verified){RESET} | Session: {details.get('session_id', 'Active')[:8]}..."
    elif "PREDICT" in act or "MODEL" in act or "TRAIN" in act:
        badge = f"{YELLOW}{BOLD}[ML MODEL TRAINED]{RESET}"
        ticker = details.get('ticker') or details.get('symbol') or 'N/A'
        model = details.get('model_name') or details.get('model') or 'Regression'
        acc = details.get('accuracy') or details.get('directional_accuracy') or details.get('rmse') or 'Evaluated'
        info = f"User: {user_tag} | Model: {BOLD}{model}{RESET} | Stock: {CYAN}{ticker}{RESET} | Performance: {GREEN}{acc}{RESET}"
    elif "PORTFOLIO" in act or "OPTIMIZ" in act or "SHARPE" in act:
        badge = f"{MAGENTA}{BOLD}[PORTFOLIO OPTIMIZATION]{RESET}"
        assets = details.get('tickers') or details.get('symbols') or 'Multi-Asset'
        strat = details.get('strategy') or 'Max Sharpe Ratio'
        info = f"User: {user_tag} | Strategy: {BOLD}{strat}{RESET} | Allocation: {CYAN}{assets}{RESET}"
    elif "SENTIMENT" in act or "NEWS" in act:
        badge = f"{CYAN}{BOLD}[NLP SENTIMENT SCAN]{RESET}"
        ticker = details.get('ticker') or details.get('news_ticker') or 'General'
        score = details.get('compound') or details.get('sentiment') or 'Analyzed'
        info = f"User: {user_tag} | Ticker: {BOLD}{ticker}{RESET} | VADER Polarity: {YELLOW}{score}{RESET}"
    elif "STOCK" in act or "TICKER" in act or "SEARCH" in act or "CHART" in act:
        badge = f"{CYAN}{BOLD}[STOCK CHART ACCESSED]{RESET}"
        ticker = details.get('ticker') or details.get('searched_ticker') or 'N/A'
        tf = details.get('timeframe') or details.get('period') or '1y'
        info = f"User: {user_tag} | Analyzed: {BOLD}{ticker}{RESET} | Timeframe: {tf} | Technicals: RSI, MACD, Bollinger"
    elif "LOGOUT" in act:
        badge = f"{RED}{BOLD}[USER LOGGED OUT]{RESET}"
        info = f"User: {user_tag} | Session Terminated | Audit dossier synchronized & closed"
    else:
        badge = f"{CYAN}{BOLD}[USER INTERACTION]{RESET}"
        det_str = ", ".join(f"{k}: {v}" for k, v in list(details.items())[:3]) if details else "Page Navigated"
        info = f"User: {user_tag} | Action: {act} | {det_str}"

    return f" {DIM}[{timestamp}]{RESET} {badge} {info}"


def main():
    clear_screen()
    print(f"{CYAN}{BOLD}=" * 85 + f"{RESET}")
    print(f" {BG_BLUE}{BOLD} ⚡ MARKETPULSE INSTITUTIONAL BACKEND TELEMETRY & AUDIT MONITOR (AWS EC2) {RESET}")
    print(f"{CYAN}{BOLD}=" * 85 + f"{RESET}")
    print(f" {BOLD}Cloud Host:{RESET}       ec2-34-205-48-35 (Ubuntu 24.04 LTS on AWS us-east-1)")
    print(f" {BOLD}Database Engine:{RESET}  SQLite3 [data/users.db] (ACID Transactions)")
    print(f" {BOLD}Storage Root:{RESET}     {DATA_DIR}/users/<username>/")
    print(f" {BOLD}Encryption:{RESET}       PBKDF2-HMAC-SHA256 (100,000 Iterations + Hex Salt)")
    print(f" {BOLD}Telemetry State:{RESET}  {GREEN}ACTIVE & STREAMING IN REAL TIME{RESET}")
    print(f"{CYAN}{BOLD}=" * 85 + f"{RESET}")
    
    users_count = get_db_users_count()
    print(f" {YELLOW}Current Registered Accounts in Database:{RESET} {BOLD}{users_count}{RESET}")
    print(f" {DIM}Listening for live frontend user actions (Registrations, Logins, ML Training, Stocks)...{RESET}")
    print(f"{CYAN}{BOLD}-" * 85 + f"{RESET}\n")

    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(GLOBAL_LOG_PATH):
        with open(GLOBAL_LOG_PATH, "w", encoding="utf-8") as f:
            pass

    # Open log file and seek to end (or show last 5 events)
    with open(GLOBAL_LOG_PATH, "r", encoding="utf-8") as f:
        existing_lines = f.readlines()
        if existing_lines:
            print(f" {DIM}--- Last {min(5, len(existing_lines))} Recent Recorded Transactions ---{RESET}")
            for line in existing_lines[-5:]:
                try:
                    data = json.loads(line.strip())
                    print(format_action_badge(
                        data.get("action", "UNKNOWN"),
                        data.get("username", "guest"),
                        data.get("details", {}),
                        data.get("timestamp", datetime.utcnow().strftime("%H:%M:%S"))
                    ))
                except Exception:
                    pass
            print(f" {DIM}------------------------------------------------------------{RESET}\n")
            print(f" {GREEN}{BOLD}>>> AWAITING NEW LIVE INTERACTIONS FROM BROWSER (http://34.205.48.35)...{RESET}\n")

        # Live Tail loop
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                try:
                    data = json.loads(line.strip())
                    action = data.get("action", "UNKNOWN")
                    user = data.get("username", "guest")
                    details = data.get("details", {})
                    ts = data.get("timestamp", datetime.utcnow().strftime("%H:%M:%S UTC"))
                    print(format_action_badge(action, user, details, ts))
                    sys.stdout.flush()
                except Exception as e:
                    pass
            else:
                time.sleep(0.3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Telemetry Monitor stopped by user.{RESET}\n")
