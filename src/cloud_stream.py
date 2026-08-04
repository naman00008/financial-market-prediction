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

STREAM_TOPIC = "marketpulse_live_audit_stream_naman_v2"
PUBLISH_URL = f"https://ntfy.sh/{STREAM_TOPIC}"
STREAM_URL = f"https://ntfy.sh/{STREAM_TOPIC}/raw"
POLL_URL = f"https://ntfy.sh/{STREAM_TOPIC}/raw?poll=1&since=1h"


def _send_payload_async(payload: Dict[str, Any]) -> None:
    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            PUBLISH_URL,
            data=data_bytes,
            headers={
                "Title": f"User Action: {payload.get('username', 'guest')}",
                "User-Agent": "MarketPulseAuditRelay/2.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=8):
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
    Automatically reconnects on network interruptions.
    """
    # 1. Fetch recent events on startup
    try:
        req = urllib.request.Request(POLL_URL, headers={"User-Agent": "MarketPulseClient/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            for line in content.splitlines():
                if line.strip():
                    try:
                        ev = json.loads(line.strip())
                        on_event(ev)
                    except Exception:
                        pass
    except Exception:
        pass

    # 2. Continuous real-time stream
    while True:
        try:
            req = urllib.request.Request(STREAM_URL, headers={"User-Agent": "MarketPulseClient/2.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if line:
                        try:
                            event_obj = json.loads(line)
                            on_event(event_obj)
                        except Exception:
                            pass
        except Exception:
            time.sleep(2)
