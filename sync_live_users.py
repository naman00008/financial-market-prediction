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

LIVE_API_URL = "https://financial-market-prediction.onrender.com/api/sync"
FALLBACK_ZIP_URL = "https://financial-market-prediction.onrender.com/api/download_users"


def perform_sync(silent: bool = False) -> bool:
    req = urllib.request.Request(
        LIVE_API_URL,
        headers={"User-Agent": "MarketPulseLiveSync/2.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_data = resp.read().decode("utf-8")
            data = json.loads(raw_data)

        if data.get("status") == "success":
            count = apply_backend_data_bundle(data)
            if not silent:
                print(f"[{time.strftime('%H:%M:%S')}] ✅ Synced {count} user folder(s) from cloud website:")
                for u in sorted(data.get("users", {}).keys()):
                    print(f"   • @{u}")
            return True
        else:
            if not silent:
                print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Server response: {data}")
            return False

    except urllib.error.HTTPError as e:
        if not silent:
            print(f"[{time.strftime('%H:%M:%S')}] ⏳ Cloud server is updating (HTTP {e.code})...")
        return False
    except urllib.error.URLError as e:
        if not silent:
            print(f"[{time.strftime('%H:%M:%S')}] ⏳ Connecting to cloud server ({e.reason})...")
        return False
    except Exception as e:
        if not silent:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Sync notice: {e}")
        return False


def main():
    live_mode = "--live" in sys.argv or "--watch" in sys.argv

    print("\n" + "=" * 70)
    print(" 🔄 MARKETPULSE CLOUD BACKEND SYNCHRONIZER")
    print("=" * 70)
    print(f" Target Local Folder: {USERS_DIR}")
    print(f" Source Cloud URL:    {LIVE_API_URL}")
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
