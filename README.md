# OpenCode-like Autonomous Coding Assistant MVP

## 1) Executive summary
This repository contains a runnable MVP for an OpenCode-like autonomous coding assistant platform with a safety-first architecture. It includes:
- A FastAPI **Orchestrator** with planning, policy checks, tool execution, and append-only audit logging.
- A local FastAPI **Desktop Agent** with localhost authentication, explicit user confirmation semantics, and strict admin command allow-listing.
- A minimal browser UI for plan generation, tool approval, and execution of an end-to-end `workspace.apply_patch` flow.
- Typed, explicit tool metadata (`intent`, `risk_level`, `requires_confirmation`, `rollback_plan`) and policy boundaries.

## 2) PRD-lite (bullets)
### User stories
- As a developer, I can describe a coding task and receive a clear multi-step plan.
- As a developer, I can preview high-risk actions and explicitly approve before execution.
- As a security-conscious user, I can see an immutable audit trail of tool calls and file changes.
- As an advanced user, I can enable a local Desktop Agent and grant admin-session access only after clear confirmation.
- As a researcher, I can fetch docs from approved web domains with citation-friendly snippets.

### MVP features
- Plan endpoint (`/api/plan`) returning milestones + acceptance criteria.
- Tool registry with typed descriptors and risk metadata.
- Workspace tools:
  - list/read/write/apply_patch/run_command
- Web connector (`web.fetch_url`) with domain allow-list.
- Desktop Agent tools proxied by orchestrator:
  - `system.request_admin_session`
  - `admin.run_command` (allow-list gated)
- Append-only JSONL audit log (`audit.log.jsonl`).
- Minimal UI with preview/approval action model.

### Non-goals (v1)
- Hidden background persistence
- Arbitrary network scanning
- Access outside user-granted workspace
- Privilege escalation bypasses or prompt spoofing

### Acceptance criteria
- Unsafe/destructive actions cannot run without explicit approval.
- All workspace file paths are constrained to workspace root.
- Tool execution emits auditable records.
- Admin flows require local auth token + explicit user-confirmed session.
- Web fetch fails for non-allow-listed domains.

## 3) Technical spec (bullets + ASCII diagram)
### Architecture diagram
```text
User
  |
  v
[Minimal UI] ---> [Orchestrator API]
                     |   |    |
                     |   |    +--> [Audit Logger JSONL]
                     |   +-------> [Provider/Planner Loop (MVP stub)]
                     +-----------> [Tool Registry + Policy Engine]
                                      |         |         |
                                      |         |         +--> [Web Connector (allow-list)]
                                      |         +------------> [Workspace Tools]
                                      +----------------------> [Desktop Agent RPC localhost]
                                                                 |
                                                                 +--> [Admin Session + Allow-list]
```

### Module responsibilities
- `services/orchestrator/main.py`
  - API routes for planning, listing tools, and executing tools.
  - Approval gate behavior for high-risk tools.
- `services/orchestrator/policy.py`
  - Enforces workspace path boundaries and destructive-action policy rules.
- `services/orchestrator/tool_registry.py`
  - Tool metadata and dispatch to concrete runners.
- `services/orchestrator/workspace_tools.py`
  - File/patch/command operations constrained by policy and audited.
- `services/orchestrator/web_tools.py`
  - Allow-list validated URL fetch.
- `services/orchestrator/desktop_client.py`
  - Localhost RPC client for Desktop Agent admin flow.
- `services/desktop_agent/main.py`
  - Local auth token, admin session issuance, allow-listed admin command endpoint.

### Security model
- Default deny outside `workspace/` root.
- Destructive actions marked as `requires_confirmation` and blocked until approved.
- Desktop Agent is localhost-only and token-authenticated.
- Admin session issuance requires explicit `user_confirmed=true` and reason string.
- Admin commands must match explicit allow-list.
- No secrets are logged in this MVP (token comes from env/runtime).

### Audit/logging strategy
- JSONL append-only log file (`audit.log.jsonl`).
- Every tool invocation writes:
  - `audit_event_id`
  - timestamp
  - tool name
  - intent
  - risk level
  - confirmation requirement
  - args (non-secret)
  - rollback plan (if any)

## 4) Tool schemas (JSON code blocks)
```json
{
  "name": "workspace.list_files",
  "input_schema": {
    "type": "object",
    "properties": {
      "rel_dir": { "type": "string", "default": "." }
    }
  },
  "output": ["audit_event_id", "files"],
  "risk_level": "low",
  "requires_confirmation": false
}
```

```json
{
  "name": "workspace.read_file",
  "input_schema": {
    "type": "object",
    "properties": {
      "rel_path": { "type": "string" }
    },
    "required": ["rel_path"]
  },
  "output": ["audit_event_id", "content"],
  "risk_level": "low",
  "requires_confirmation": false
}
```

```json
{
  "name": "workspace.write_file",
  "input_schema": {
    "type": "object",
    "properties": {
      "rel_path": { "type": "string" },
      "content": { "type": "string" }
    },
    "required": ["rel_path", "content"]
  },
  "output": ["audit_event_id", "written"],
  "risk_level": "medium",
  "requires_confirmation": true,
  "rollback_plan": "Restore previous file content"
}
```

```json
{
  "name": "workspace.apply_patch",
  "input_schema": {
    "type": "object",
    "properties": {
      "rel_path": { "type": "string" },
      "before": { "type": "string" },
      "after": { "type": "string" }
    },
    "required": ["rel_path", "before", "after"]
  },
  "output": ["audit_event_id", "patched"],
  "risk_level": "medium",
  "requires_confirmation": true,
  "rollback_plan": "Re-apply previous content"
}
```

```json
{
  "name": "workspace.run_command",
  "input_schema": {
    "type": "object",
    "properties": {
      "cmd": { "type": "string" },
      "cwd": { "type": "string", "default": "." },
      "timeout": { "type": "integer", "default": 30 }
    },
    "required": ["cmd"]
  },
  "output": ["audit_event_id", "returncode", "stdout", "stderr"],
  "risk_level": "high",
  "requires_confirmation": true
}
```

```json
{
  "name": "system.request_admin_session",
  "input_schema": {
    "type": "object",
    "properties": {
      "reason": { "type": "string" },
      "user_confirmed": { "type": "boolean" }
    },
    "required": ["reason", "user_confirmed"]
  },
  "output": ["session_id", "status"],
  "risk_level": "high",
  "requires_confirmation": true
}
```

```json
{
  "name": "admin.run_command",
  "input_schema": {
    "type": "object",
    "properties": {
      "session_id": { "type": "string" },
      "command": { "type": "string" }
    },
    "required": ["session_id", "command"]
  },
  "output": ["status", "command"],
  "risk_level": "high",
  "requires_confirmation": true
}
```

```json
{
  "name": "web.fetch_url",
  "input_schema": {
    "type": "object",
    "properties": {
      "url": { "type": "string", "format": "uri" }
    },
    "required": ["url"]
  },
  "output": ["audit_event_id", "url", "status_code", "content_snippet"],
  "risk_level": "medium",
  "requires_confirmation": true
}
```

## 5) Repo structure (tree)
```text
.
├── README.md
├── requirements.txt
├── docs/
│   └── sample_session.md
├── services/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── audit.py
│   │   ├── desktop_client.py
│   │   ├── main.py
│   │   ├── policy.py
│   │   ├── tool_registry.py
│   │   ├── web_tools.py
│   │   ├── workspace_tools.py
│   │   └── templates/
│   │       └── index.html
│   └── desktop_agent/
│       ├── __init__.py
│       └── main.py
└── tests/
    └── test_policy.py
```

## 6) Implementation steps
1. Create orchestrator API with planning and tool execution routes.
2. Add policy engine for workspace boundary and explicit approval controls.
3. Build workspace/web/admin tool adapters.
4. Build desktop agent with local token and admin command allow-list.
5. Add append-only audit log writer.
6. Add minimal UI for plan and patch approval flow.
7. Add tests for critical policy and path safety behavior.

## 7) Code skeleton (multiple files)
See files under `services/`, `tests/`, and this README's tree.

## 8) Setup + run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Terminal A: Desktop agent
uvicorn services.desktop_agent.main:app --host 127.0.0.1 --port 8787

# Obtain session token (copy output)
curl http://127.0.0.1:8787/session

# Terminal B: Orchestrator
export DESKTOP_AGENT_TOKEN=<token_from_session_endpoint>
uvicorn services.orchestrator.main:app --host 0.0.0.0 --port 8000
```
Open `http://127.0.0.1:8000`.

## Security notes
- Destructive tool calls are blocked unless `approved=true`.
- File access is restricted to `./workspace`.
- Desktop Agent accepts localhost token-authenticated requests only.
- Admin commands are strictly allow-listed and session-gated.

## Provider integration note
Provider routing is designed as an extension point in orchestrator; for this MVP, plan generation is deterministic and local.

## Desktop Agent consent flow
1. User explicitly requests admin action.
2. UI sends `system.request_admin_session` with `user_confirmed=true` and reason.
3. Desktop Agent returns `session_id`.
4. `admin.run_command` requires that `session_id` and command allow-list match.
5. Any true elevated execution should be delegated to OS-native prompt flow in production.
