"""
MarketPulse One-Click Instant Cloud Backend & Database Synchronizer
Fetches all user accounts, credentials, activity logs, predictions, and SQLite records
from the live cloud website into the local backend.
"""

import os
import sys
import requests
from src.auth import sync_db_and_folders, get_db_connection, DB_PATH
from src.tracker import apply_backend_data_bundle, USERS_DIR

def main():
    print("\n" + "=" * 80)
    print(" MARKETPULSE INSTANT DATABASE & BACKEND SYNCHRONIZER")
    print("=" * 80)
    print(f" Local SQLite DB: {DB_PATH}")
    print(f" User Directory:  {USERS_DIR}")
    print("=" * 80)
    print(" Fetching latest cloud user accounts and activity dossiers from Render...")

    cloud_endpoints = [
        "https://financial-market-prediction.onrender.com/api/sync",
        "https://financial-market-prediction.onrender.com/app/static/live_users_sync.json"
    ]

    synced = False
    for url in cloud_endpoints:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200 and r.text.strip():
                data = r.json()
                count = apply_backend_data_bundle(data)
                print(f" [OK] Successfully imported {count} cloud user accounts and activity folders.")
                synced = True
                break
        except Exception as e:
            continue

    if not synced:
        print(" [INFO] Cloud API unreachable or cold start. Running local bidirectional database sync...")

    # Run local bidirectional database & folder sync
    sync_db_and_folders()

    # Display current database users
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, full_name, tier, created_at FROM users ORDER BY id ASC")
        rows = cursor.fetchall()
        print("\n" + "=" * 80)
        print(f" CURRENT DATABASE USERS ({len(rows)} Registered Accounts):")
        print("=" * 80)
        for r in rows:
            print(f" • [ID: {r['id']:02d}] @{r['username']:<16} | {r['full_name']:<20} | {r['email']:<28} | {r['tier'].upper()}")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
