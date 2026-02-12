from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .policy import PolicyEngine
from .desktop_client import DesktopClient
from .tool_registry import ToolRegistry
from .web_tools import WebTools
from .workspace_tools import WorkspaceTools


class PlanRequest(BaseModel):
    goal: str = Field(min_length=5)


class ToolExecutionRequest(BaseModel):
    tool_name: str
    args: dict[str, Any]
    approved: bool = False


app = FastAPI(title="OpenCode-like Orchestrator MVP", version="0.1.0")

workspace_root = Path.cwd() / "workspace"
workspace_root.mkdir(exist_ok=True)
policy = PolicyEngine(workspace_root=workspace_root)
audit_path = Path.cwd() / "audit.log.jsonl"

workspace_tools = WorkspaceTools(workspace_root=workspace_root, audit_log_path=audit_path, policy=policy)
web_tools = WebTools(audit_log_path=audit_path, allowlist={"docs.python.org", "fastapi.tiangolo.com"})
desktop_client = DesktopClient()
tool_registry = ToolRegistry(workspace_tools=workspace_tools, web_tools=web_tools, desktop_client=desktop_client)

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "templates")), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    with open(Path(__file__).parent / "templates" / "index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/plan")
def create_plan(req: PlanRequest) -> dict[str, Any]:
    return {
        "goal": req.goal,
        "milestones": [
            "Analyze workspace and constraints",
            "Propose patch and command plan",
            "Apply approved changes",
            "Run verification",
        ],
        "acceptance_criteria": [
            "All file writes stay in workspace",
            "High-risk actions require approval",
            "Audit events are appended",
        ],
    }


@app.get("/api/tools")
def list_tools() -> dict[str, Any]:
    return {"tools": tool_registry.describe_tools()}


@app.post("/api/execute")
def execute_tool(req: ToolExecutionRequest) -> dict[str, Any]:
    descriptor = tool_registry.get_descriptor(req.tool_name)
    if descriptor is None:
        raise HTTPException(status_code=404, detail="Unknown tool")

    if descriptor.requires_confirmation and not req.approved:
        return {
            "status": "awaiting_approval",
            "tool": req.tool_name,
            "intent": descriptor.intent,
            "risk_level": descriptor.risk_level,
            "requires_confirmation": True,
        }

    try:
        result = tool_registry.execute(req.tool_name, req.args)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "status": "ok",
        "tool": req.tool_name,
        "intent": descriptor.intent,
        "risk_level": descriptor.risk_level,
        "requires_confirmation": descriptor.requires_confirmation,
        "result": result,
    }
