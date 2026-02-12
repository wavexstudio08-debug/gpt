from pathlib import Path

import pytest

from services.orchestrator.policy import PolicyEngine


def test_workspace_boundary_enforced(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    policy = PolicyEngine(workspace)

    policy.enforce_workspace_path(workspace / "ok.txt")
    with pytest.raises(PermissionError):
        policy.enforce_workspace_path(tmp_path / "outside.txt")


def test_destructive_action_requires_approval(tmp_path: Path) -> None:
    policy = PolicyEngine(tmp_path)
    with pytest.raises(PermissionError):
        policy.check_destructive_action("workspace.apply_patch", approved=False)

    policy.check_destructive_action("workspace.apply_patch", approved=True)
