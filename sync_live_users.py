"""
Live Cloud-to-Local User Directory Synchronizer
Fetches all live user registrations, directories, activity reports, and spreadsheets
from the deployed website on Render directly into your local Mac's `data/users/` directory.

Usage:
    python3 sync_live_users.py          # Run once to sync all users immediately
    python3 sync_live_users.py --live   # Continuous live sync mode (every 5 seconds)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from src.tracker import apply_backend_data_bundle, USERS_DIR

PRIMARY_URL = "https://financial-market-prediction.onrender.com/app/static/users_sync.json"
SECONDARY_URL = "https://financial-market-prediction.onrender.com/api/sync"


def fetch_from_url(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MarketPulseLiveSync/2.0"}
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        raw_data = resp.read().decode("utf-8")
        return json.loads(raw_data)


def perform_sync(silent: bool = False) -> bool:
    data = None
    last_err = None

    for url in [PRIMARY_URL, SECONDARY_URL]:
        try:
            data = fetch_from_url(url)
            if data and data.get("status") == "success":
                break
        except Exception as e:
            last_err = e
            continue

    if data and data.get("status") == "success":
        count = apply_backend_data_bundle(data)
        if not silent:
            print(f"[{time.strftime('%H:%M:%S')}] ✅ Synced {count} live user folder(s) from cloud:")
            for u in sorted(data.get("users", {}).keys()):
                print(f"   • 📁 @{u}")
        return True
    else:
        if not silent:
            if isinstance(last_err, urllib.error.HTTPError):
                if last_err.code == 404:
                    print(f"[{time.strftime('%H:%M:%S')}] ⏳ Cloud deployment is finalizing... (HTTP 404)")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] ⏳ Cloud server status: HTTP {last_err.code}")
            elif isinstance(last_err, urllib.error.URLError):
                print(f"[{time.strftime('%H:%M:%S')}] ⏳ Connecting to cloud server ({last_err.reason})...")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ⏳ Waiting for cloud update ({last_err})...")
        return False


def main():
    live_mode = "--live" in sys.argv or "--watch" in sys.argv

    print("\n" + "=" * 70)
    print(" 🔄 MARKETPULSE CLOUD BACKEND SYNCHRONIZER")
    print("=" * 70)
    print(f" Target Local Folder: {USERS_DIR}")
    print(f" Source Cloud URL:    {PRIMARY_URL}")
    print("=" * 70)

    if live_mode:
        print(" 🟢 LIVE REAL-TIME SYNC MODE ACTIVE (Polling every 5s)")
        print(" Press Ctrl+C to stop.\n")
        try:
            while True:
                perform_sync(silent=False)
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n Live sync stopped.")
    else:
        perform_sync(silent=False)
        print("\n✅ Sync complete. Open Finder -> data/users/ to inspect user dossiers!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
