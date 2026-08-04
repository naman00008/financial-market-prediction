"""
Real-Time Cloud Audit Stream Bridge
Enables sub-second live streaming of user activities and folder synchronization
between any browser/client on the internet and the Mac backend terminal.
"""

import json
import os
import threading
import time
from typing import Any, Callable, Dict, Optional
import requests
import warnings

# Suppress urllib3 LibreSSL warning for clean terminal
warnings.filterwarnings("ignore", category=UserWarning)

STREAM_TOPIC = "marketpulse_live_audit_stream_naman_v3"
MIRROR_TOPIC = "marketpulse_naman_live_stream"
PUBLISH_URLS = [
    f"https://ntfy.sh/{STREAM_TOPIC}",
    f"https://ntfy.sh/{MIRROR_TOPIC}"
]
STREAM_JSON_URL = f"https://ntfy.sh/{STREAM_TOPIC}/json"
POLL_JSON_URL = f"https://ntfy.sh/{STREAM_TOPIC}/json?poll=1&since=24h"


def _send_payload_async(payload: Dict[str, Any]) -> None:
    for url in PUBLISH_URLS:
        try:
            requests.post(
                url,
                json=payload,
                headers={"Title": f"User Action: {payload.get('username', 'guest')}"},
                timeout=5
            )
        except Exception:
            pass


def publish_cloud_event(
    action: str,
    username: str,
    details: Optional[Dict[str, Any]] = None,
    user_profile: Optional[Dict[str, Any]] = None
) -> None:
    """Send live event to cloud pub/sub stream in non-blocking background thread."""
    payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "epoch": time.time(),
        "username": username or "guest",
        "action": action,
        "details": details or {},
        "user_profile": user_profile or {}
    }
    t = threading.Thread(target=_send_payload_async, args=(payload,), daemon=True)
    t.start()


def _parse_and_dispatch(line_str: str, on_event: Callable[[Dict[str, Any]], None]) -> None:
    try:
        obj = json.loads(line_str)
        if obj.get("event") == "message" and "message" in obj:
            msg_raw = obj["message"]
            if isinstance(msg_raw, str):
                inner_msg = json.loads(msg_raw)
            else:
                inner_msg = msg_raw
            on_event(inner_msg)
    except Exception:
        pass


def listen_live_stream(on_event: Callable[[Dict[str, Any]], None]) -> None:
    """
    Connect to real-time live event stream using requests.iter_lines().
    Sub-second latency with automatic 24-hour catch-up on launch.
    """
    # 1. Catch-up poll from past 24 hours
    try:
        r = requests.get(POLL_JSON_URL, timeout=10)
        if r.status_code == 200:
            for line in r.text.splitlines():
                line = line.strip()
                if line:
                    _parse_and_dispatch(line, on_event)
    except Exception:
        pass

    # 2. Continuous real-time stream
    while True:
        try:
            with requests.get(STREAM_JSON_URL, stream=True, timeout=120) as resp:
                for raw_line in resp.iter_lines():
                    if raw_line:
                        decoded = raw_line.decode("utf-8").strip()
                        if decoded:
                            _parse_and_dispatch(decoded, on_event)
        except Exception:
            time.sleep(1)
