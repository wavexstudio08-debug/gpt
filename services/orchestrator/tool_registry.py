from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .desktop_client import DesktopClient
from .web_tools import WebTools
from .workspace_tools import WorkspaceTools


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    intent: str
    risk_level: str
    requires_confirmation: bool
    rollback_plan: str | None


class ToolRegistry:
    def __init__(self, workspace_tools: WorkspaceTools, web_tools: WebTools, desktop_client: DesktopClient):
        self.workspace_tools = workspace_tools
        self.web_tools = web_tools
        self.desktop_client = desktop_client
        self._descriptors: dict[str, ToolDescriptor] = {
            "workspace.list_files": ToolDescriptor("workspace.list_files", "List files within granted workspace", "low", False, None),
            "workspace.read_file": ToolDescriptor("workspace.read_file", "Read a single file", "low", False, None),
            "workspace.write_file": ToolDescriptor("workspace.write_file", "Write file content", "medium", True, "Restore previous file content"),
            "workspace.apply_patch": ToolDescriptor("workspace.apply_patch", "Apply patch to file", "medium", True, "Revert patched file"),
            "workspace.run_command": ToolDescriptor("workspace.run_command", "Run command in workspace", "high", True, "Review command side effects"),
            "system.request_admin_session": ToolDescriptor("system.request_admin_session", "Request user-mediated admin session", "high", True, None),
            "admin.run_command": ToolDescriptor("admin.run_command", "Run strict allow-listed admin command", "high", True, "Terminate admin session"),
            "web.fetch_url": ToolDescriptor("web.fetch_url", "Fetch allow-listed web docs", "medium", True, None),
        }
        self._runners: dict[str, Callable[..., dict[str, Any]]] = {
            "workspace.list_files": self.workspace_tools.list_files,
            "workspace.read_file": self.workspace_tools.read_file,
            "workspace.write_file": self.workspace_tools.write_file,
            "workspace.apply_patch": self.workspace_tools.apply_patch,
            "workspace.run_command": self.workspace_tools.run_command,
            "system.request_admin_session": self.desktop_client.request_admin_session,
            "admin.run_command": self.desktop_client.admin_run_command,
            "web.fetch_url": self.web_tools.fetch_url,
        }

    def describe_tools(self) -> list[dict[str, Any]]:
        return [vars(d) for d in self._descriptors.values()]

    def get_descriptor(self, name: str) -> ToolDescriptor | None:
        return self._descriptors.get(name)

    def execute(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        runner = self._runners.get(name)
        if runner is None:
            raise ValueError(f"Unsupported tool {name}")
        return runner(**args)
