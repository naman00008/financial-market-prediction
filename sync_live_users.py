"""
Cloud-to-Local User Directory Synchronizer
Fetches all live user registrations, folders, activity logs, and Excel CSVs
from the deployed website on Render directly into your local Mac's `data/users/` folder.

Usage:
    python3 sync_live_users.py
"""

import json
import os
import sys
import urllib.request
import urllib.error
from src.tracker import apply_backend_data_bundle, USERS_DIR

LIVE_SYNC_URL = "https://financial-market-prediction.onrender.com/?sync_key=marketpulse_secret_sync_2026"


def sync_cloud_users():
    print("\n" + "=" * 70)
    print(" 🔄 SYNCING LIVE USERS FROM CLOUD (RENDER) TO LOCAL MAC...")
    print("=" * 70)
    print(f"Connecting to: {LIVE_SYNC_URL}")

    req = urllib.request.Request(
        LIVE_SYNC_URL,
        headers={"User-Agent": "MarketPulseSyncClient/1.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != "success":
            print(f"❌ Server returned unexpected format: {data}")
            return

        user_count = apply_backend_data_bundle(data)
        print(f"\n✅ Successfully synchronized {user_count} live user folder(s) into:")
        print(f"   📂 {USERS_DIR}\n")
        
        users = data.get("users", {})
        for uname in sorted(users.keys()):
            print(f"   • Synced user: @{uname}")

        print("\n🎉 You can now open Finder -> data/users/ to see all updated user folders!")
        print("=" * 70 + "\n")

    except urllib.error.URLError as e:
        print(f"\n❌ Connection Error: Could not reach live website ({e}).")
        print("   Please make sure the Render deployment has finished building.\n")
    except Exception as e:
        print(f"\n❌ Error during sync: {e}\n")


if __name__ == "__main__":
    sync_cloud_users()
