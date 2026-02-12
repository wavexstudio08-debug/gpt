from __future__ import annotations

import subprocess
from pathlib import Path

from .audit import write_audit_event
from .policy import PolicyEngine


class WorkspaceTools:
    def __init__(self, workspace_root: Path, audit_log_path: Path, policy: PolicyEngine):
        self.workspace_root = workspace_root
        self.audit_log_path = audit_log_path
        self.policy = policy

    def _path(self, rel_path: str) -> Path:
        target = (self.workspace_root / rel_path).resolve()
        self.policy.enforce_workspace_path(target)
        return target

    def list_files(self, rel_dir: str = ".") -> dict:
        target = self._path(rel_dir)
        files = sorted(str(p.relative_to(self.workspace_root)) for p in target.rglob("*") if p.is_file())
        event_id = write_audit_event(self.audit_log_path, {
            "tool": "workspace.list_files",
            "intent": "Inspect workspace files",
            "risk_level": "low",
            "requires_confirmation": False,
            "args": {"rel_dir": rel_dir},
        })
        return {"audit_event_id": event_id, "files": files}

    def read_file(self, rel_path: str) -> dict:
        target = self._path(rel_path)
        content = target.read_text(encoding="utf-8")
        event_id = write_audit_event(self.audit_log_path, {
            "tool": "workspace.read_file",
            "intent": "Read requested file",
            "risk_level": "low",
            "requires_confirmation": False,
            "args": {"rel_path": rel_path},
        })
        return {"audit_event_id": event_id, "content": content}

    def write_file(self, rel_path: str, content: str) -> dict:
        target = self._path(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        event_id = write_audit_event(self.audit_log_path, {
            "tool": "workspace.write_file",
            "intent": "Write file content",
            "risk_level": "medium",
            "requires_confirmation": True,
            "args": {"rel_path": rel_path},
            "rollback_plan": "Restore file from git or prior backup",
        })
        return {"audit_event_id": event_id, "written": rel_path}

    def apply_patch(self, rel_path: str, before: str, after: str) -> dict:
        target = self._path(rel_path)
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        if current != before:
            raise ValueError("Patch rejected: before content did not match current file")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(after, encoding="utf-8")
        event_id = write_audit_event(self.audit_log_path, {
            "tool": "workspace.apply_patch",
            "intent": "Apply user-approved patch",
            "risk_level": "medium",
            "requires_confirmation": True,
            "args": {"rel_path": rel_path},
            "rollback_plan": "Re-apply previous content",
        })
        return {"audit_event_id": event_id, "patched": rel_path}

    def run_command(self, cmd: str, cwd: str = ".", timeout: int = 30) -> dict:
        cwd_path = self._path(cwd)
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        event_id = write_audit_event(self.audit_log_path, {
            "tool": "workspace.run_command",
            "intent": "Run verification command",
            "risk_level": "high",
            "requires_confirmation": True,
            "args": {"cmd": cmd, "cwd": cwd, "timeout": timeout},
            "rollback_plan": "No filesystem rollback; inspect command impact",
        })
        return {
            "audit_event_id": event_id,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
