"""
Real-Time Cloud Audit Stream Bridge
Enables sub-second live streaming of user activities and folder synchronization
between any browser/client on the internet and the Mac backend terminal.
"""

import json
import os
import threading
import time
import urllib.request
import urllib.error
from typing import Any, Callable, Dict, Optional

STREAM_TOPIC = "marketpulse_live_audit_stream_naman_v3"
MIRROR_TOPIC = "marketpulse_naman_live_stream"
PUBLISH_URLS = [
    f"https://ntfy.sh/{STREAM_TOPIC}",
    f"https://ntfy.sh/{MIRROR_TOPIC}"
]
STREAM_JSON_URL = f"https://ntfy.sh/{STREAM_TOPIC}/json"
POLL_JSON_URL = f"https://ntfy.sh/{STREAM_TOPIC}/json?poll=1&since=24h"


def _send_payload_async(payload: Dict[str, Any]) -> None:
    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        for url in PUBLISH_URLS:
            try:
                req = urllib.request.Request(
                    url,
                    data=data_bytes,
                    headers={
                        "Title": f"User Action: {payload.get('username', 'guest')}",
                        "User-Agent": "MarketPulseAuditRelay/3.0"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=6):
                    pass
            except Exception:
                pass
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


def listen_live_stream(on_event: Callable[[Dict[str, Any]], None]) -> None:
    """
    Connect to real-time live event stream and invoke callback for each action.
    Automatically catches up with 24h history and maintains persistent connection.
    """
    # 1. Catch-up poll from past 24 hours
    try:
        req = urllib.request.Request(POLL_JSON_URL, headers={"User-Agent": "MarketPulseClient/3.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("event") == "message" and "message" in obj:
                        inner_msg = json.loads(obj["message"])
                        on_event(inner_msg)
                except Exception:
                    pass
    except Exception:
        pass

    # 2. Continuous real-time stream
    while True:
        try:
            req = urllib.request.Request(STREAM_JSON_URL, headers={"User-Agent": "MarketPulseClient/3.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("event") == "message" and "message" in obj:
                            inner_msg = json.loads(obj["message"])
                            on_event(inner_msg)
                    except Exception:
                        pass
        except Exception:
            time.sleep(2)
