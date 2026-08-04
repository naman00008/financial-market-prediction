#!/bin/bash
cd "$(dirname "$0")"
python3 sync_live_users.py
read -p "Press Enter to exit..."
