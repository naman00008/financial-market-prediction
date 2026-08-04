#!/bin/bash
cd "$(dirname "$0")"
echo "Starting real-time live synchronization with cloud website..."
python3 sync_live_users.py --live
read -p "Press Enter to exit..."
