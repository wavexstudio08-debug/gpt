from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Desktop Agent MVP", version="0.1.0")

SESSION_TOKEN = secrets.token_hex(16)
ADMIN_SESSION: str | None = None
WORKSPACE_ROOT = Path.cwd() / "workspace"
WORKSPACE_ROOT.mkdir(exist_ok=True)


class AdminSessionRequest(BaseModel):
    reason: str
    user_confirmed: bool


class AdminCommandRequest(BaseModel):
    session_id: str
    command: str


ALLOWLIST = {"whoami", "id", "uname -a"}


def require_auth(token: str | None) -> None:
    if token != SESSION_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid local agent token")


@app.get("/session")
def session() -> dict[str, str]:
    return {"token": SESSION_TOKEN}


@app.post("/system/request_admin_session")
def request_admin_session(req: AdminSessionRequest, x_agent_token: str | None = Header(default=None)) -> dict[str, str]:
    require_auth(x_agent_token)
    if not req.user_confirmed:
        raise HTTPException(status_code=403, detail="User confirmation required")
    if len(req.reason.strip()) < 10:
        raise HTTPException(status_code=400, detail="Reason must be explicit")

    global ADMIN_SESSION
    ADMIN_SESSION = secrets.token_hex(12)
    return {"session_id": ADMIN_SESSION, "status": "granted_by_user"}


@app.post("/admin/run_command")
def admin_run_command(req: AdminCommandRequest, x_agent_token: str | None = Header(default=None)) -> dict[str, str]:
    require_auth(x_agent_token)
    if req.session_id != ADMIN_SESSION:
        raise HTTPException(status_code=403, detail="Admin session required")
    if req.command not in ALLOWLIST:
        raise HTTPException(status_code=403, detail="Command not in admin allow-list")
    return {"status": "approved_for_os_prompt", "command": req.command}
