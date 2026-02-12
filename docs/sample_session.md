# Sample session transcript

## User goal
"Update hello.txt greeting and verify tests"

## Plan
1. Analyze workspace and constraints.
2. Propose patch to `hello.txt`.
3. Request approval, apply patch.
4. Run verification command.

## Approval prompt
Tool: `workspace.apply_patch`
Risk: `medium`
Requires confirmation: `true`
Intent: Apply user-approved patch.

## Patch applied
- before: `Hello`
- after: `Hello from OpenCode-like MVP`

## Tests run
- command: `python -m pytest -q`
- result: pass

## Audit log entry (example)
```json
{
  "audit_event_id": "...",
  "timestamp": "2026-01-01T00:00:00Z",
  "tool": "workspace.apply_patch",
  "intent": "Apply user-approved patch",
  "risk_level": "medium",
  "requires_confirmation": true,
  "args": {"rel_path": "hello.txt"},
  "rollback_plan": "Re-apply previous content"
}
```
