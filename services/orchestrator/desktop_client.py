from __future__ import annotations

import os

import httpx


class DesktopClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("DESKTOP_AGENT_URL", "http://127.0.0.1:8787")
        self.token = os.getenv("DESKTOP_AGENT_TOKEN", "")

    def request_admin_session(self, reason: str, user_confirmed: bool) -> dict:
        res = httpx.post(
            f"{self.base_url}/system/request_admin_session",
            json={"reason": reason, "user_confirmed": user_confirmed},
            headers={"x-agent-token": self.token},
            timeout=20,
        )
        res.raise_for_status()
        return res.json()

    def admin_run_command(self, session_id: str, command: str) -> dict:
        res = httpx.post(
            f"{self.base_url}/admin/run_command",
            json={"session_id": session_id, "command": command},
            headers={"x-agent-token": self.token},
            timeout=20,
        )
        res.raise_for_status()
        return res.json()
