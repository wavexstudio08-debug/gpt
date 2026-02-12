from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def write_audit_event(log_path: Path, event: dict) -> str:
    event_id = str(uuid4())
    payload = {
        "audit_event_id": event_id,
        "timestamp": datetime.now(UTC).isoformat(),
        **event,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
    return event_id
