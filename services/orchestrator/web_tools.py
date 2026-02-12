from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import httpx

from .audit import write_audit_event


class WebTools:
    def __init__(self, audit_log_path: Path, allowlist: set[str]):
        self.audit_log_path = audit_log_path
        self.allowlist = allowlist

    def fetch_url(self, url: str) -> dict:
        host = urlparse(url).netloc
        if host not in self.allowlist:
            raise PermissionError(f"Domain {host} is not in web allow-list")
        with httpx.Client(timeout=20) as client:
            resp = client.get(url)
            resp.raise_for_status()
        event_id = write_audit_event(self.audit_log_path, {
            "tool": "web.fetch_url",
            "intent": "Fetch user-approved documentation",
            "risk_level": "medium",
            "requires_confirmation": True,
            "args": {"url": url},
        })
        return {"audit_event_id": event_id, "url": url, "status_code": resp.status_code, "content_snippet": resp.text[:500]}
