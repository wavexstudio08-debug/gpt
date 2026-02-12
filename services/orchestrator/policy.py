from __future__ import annotations

from pathlib import Path


class PolicyEngine:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()

    def enforce_workspace_path(self, path: Path) -> None:
        resolved = path.resolve()
        if self.workspace_root not in [resolved, *resolved.parents]:
            raise PermissionError(f"Path {resolved} is outside workspace root {self.workspace_root}")

    def check_destructive_action(self, action: str, approved: bool) -> None:
        destructive = {"workspace.write_file", "workspace.apply_patch", "workspace.run_command", "workspace.delete_file"}
        if action in destructive and not approved:
            raise PermissionError(f"Action {action} requires explicit approval")
