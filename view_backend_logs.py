"""
Backend User Activity & Audit Inspector Tool
Run this script to inspect all registered user folders, profiles,
and real-time chronological activity streams across the platform.

Usage:
    python view_backend_logs.py
    python view_backend_logs.py --user <username>
    python view_backend_logs.py --tail
"""

import argparse
import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
USERS_DIR = os.path.join(BASE_DIR, "data", "users")
LOGS_DIR = os.path.join(BASE_DIR, "data", "logs")
GLOBAL_LOG_PATH = os.path.join(LOGS_DIR, "activity_stream.jsonl")


def display_all_users():
    print("\n" + "=" * 70)
    print(" 📊 REGISTERED USER DIRECTORIES & PROFILES")
    print("=" * 70)
    
    if not os.path.exists(USERS_DIR) or not os.listdir(USERS_DIR):
        print("  [No user directories found in data/users/]")
        return

    for uname in sorted(os.listdir(USERS_DIR)):
        user_dir = os.path.join(USERS_DIR, uname)
        if not os.path.isdir(user_dir):
            continue
            
        prof_file = os.path.join(user_dir, "profile.json")
        act_file = os.path.join(user_dir, "activity_logs", "activity.jsonl")
        
        act_count = 0
        if os.path.exists(act_file):
            try:
                with open(act_file, "r", encoding="utf-8") as f:
                    act_count = sum(1 for line in f if line.strip())
            except Exception:
                pass
                
        email = "N/A"
        full_name = "N/A"
        tier = "free"
        registered = "N/A"
        last_active = "N/A"
        
        if os.path.exists(prof_file):
            try:
                with open(prof_file, "r", encoding="utf-8") as f:
                    p = json.load(f)
                    email = p.get("email", "N/A")
                    full_name = p.get("full_name", "N/A")
                    tier = p.get("tier", "free")
                    registered = p.get("registered_at", "N/A")
                    last_active = p.get("last_active", "N/A")
            except Exception:
                pass

        print(f"\n📂 User Folder: data/users/{uname}/")
        print(f"   • Name:         {full_name}")
        print(f"   • Username:     @{uname}")
        print(f"   • Email:        {email}")
        print(f"   • Tier:         {tier.upper()}")
        print(f"   • Registered:   {registered}")
        print(f"   • Last Active:  {last_active}")
        print(f"   • Total Events: {act_count} recorded actions")


def display_user_activity(username: str, limit: int = 30):
    safe_uname = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
    act_file = os.path.join(USERS_DIR, safe_uname, "activity_logs", "activity.jsonl")
    
    print("\n" + "=" * 70)
    print(f" 🔍 AUDIT LOG FOR USER: @{safe_uname}")
    print("=" * 70)
    
    if not os.path.exists(act_file):
        print(f"  [No activity logs found for user @{safe_uname} at {act_file}]")
        return

    lines = []
    with open(act_file, "r", encoding="utf-8") as f:
        for l in f:
            if l.strip():
                lines.append(json.loads(l.strip()))

    if not lines:
        print("  [No actions recorded yet]")
        return

    print(f"Showing last {min(limit, len(lines))} of {len(lines)} actions:\n")
    for entry in lines[-limit:][::-1]:
        ts = entry.get("timestamp", "N/A")
        action = entry.get("action", "UNKNOWN")
        details = json.dumps(entry.get("details", {}))
        print(f"  [{ts}] {action:<24} | Details: {details}")


def display_global_activity_stream(limit: int = 40):
    print("\n" + "=" * 70)
    print(" 🌐 GLOBAL LIVE USER ACTIVITY STREAM")
    print("=" * 70)
    
    if not os.path.exists(GLOBAL_LOG_PATH):
        print("  [No global activity recorded yet at data/logs/activity_stream.jsonl]")
        return

    lines = []
    with open(GLOBAL_LOG_PATH, "r", encoding="utf-8") as f:
        for l in f:
            if l.strip():
                lines.append(json.loads(l.strip()))

    if not lines:
        print("  [No events found]")
        return

    print(f"Showing last {min(limit, len(lines))} global platform actions:\n")
    for entry in lines[-limit:][::-1]:
        ts = entry.get("timestamp", "N/A")
        user = entry.get("username", "guest")
        action = entry.get("action", "UNKNOWN")
        details = json.dumps(entry.get("details", {}))
        print(f"  [{ts}] @{user:<15} -> {action:<22} | {details}")


def main():
    parser = argparse.ArgumentParser(description="MarketPulse Backend User Activity Inspector")
    parser.add_argument("--user", "-u", type=str, help="Username to view specific activity history")
    parser.add_argument("--tail", "-t", action="store_true", help="View global activity feed")
    args = parser.parse_args()

    if args.user:
        display_user_activity(args.user)
    elif args.tail:
        display_global_activity_stream()
    else:
        display_all_users()
        display_global_activity_stream(limit=15)
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
