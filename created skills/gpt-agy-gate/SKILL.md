---
name: create-gpt-agy-gate
description: "Run a Codex PM and Antigravity implementation gate for scoped workspace tasks: create a task packet, dispatch one implementation round, audit real files, issue revisions, and approve only after quality gates pass."
---

# Create GPT AGY Gate

Use this skill for any scoped implementation, repair, migration, documentation, content, data, or automation task where Codex must coordinate Antigravity CLI and personally audit the result. The domain, workspace, files, tests, and acceptance criteria are supplied per task; do not assume a particular product or subject area.

## Roles

- Codex is PM and auditor. It owns scope, packet creation, acceptance criteria, revision decisions, and final verdict.
- Antigravity CLI is implementer and reporter. It edits only the assigned scope and never approves its own work.
- The bridge is a one-shot attempt runner (`bridge.py`). It enforces OS locks, trims old streams via FIFO, executes `agy` once, records the response, and exits.

## Required Operating Model

1. Read workspace `AGENTS.md` and `references/PROTOCOL.md`.
2. Mailbox (`chat.md`) maintains a maximum of 3 task streams (FIFO). New root tasks automatically prune older streams.
3. Create one task packet with:
   - `id`, `status=queued`, `created=<ISO-timestamp>`
   - `TASK_VERSION: 1`, `PARENT_TASK: none` (or parent ID if revision)
   - `ROUND: 1`, `MAX_ROUNDS: <positive integer>`
   - `TIMEOUT_SECONDS: <seconds>`
   - `MAX_SUBAGENT_CALLS: <integer>`, `MAX_PARALLEL_AGENTS: 1`
   - `ACCEPTANCE_MODE: delegated` (Codex approves) or `user_required` (Codex verifies, User approves)
   - Scope, Do, Do not, Definition of Done, Verification, Agent policy, and Report format.
4. Run one bridge attempt:

   `python3 .antigravity/agy-bridge/bridge.py` (or `python3 <skill-dir>/scripts/bridge.py`)

5. Keep the active Codex turn open while Antigravity runs. Antigravity delivers response into `chat.md` and state moves to `waiting-review`.
6. Inspect working tree and run 3-layer audit (Machine checks → Diff/scope → Risk sample).
7. If any gate fails and `ROUND < MAX_ROUNDS`, write a revision packet with incremented `ROUND` and run bridge again.
8. Mark `approved` (or `verified` under `user_required`) only when all criteria pass. If round limit is reached without passing, mark `stopped` with `MAX_ROUNDS_EXHAUSTED`.

## Report Format Mandate

Antigravity must return only the 5 standard fields:
- `Changed`: exact files and changes.
- `Verified`: commands run, results, and exit codes.
- `Evidence`: artifacts or proof outputs.
- `Remaining`: `none` or concrete blockers.
- `Decision`: `none` or explicit decisions needed.

## Supporting References

- [references/PROTOCOL.md](references/PROTOCOL.md): Master bridge protocol rules.
- [references/task-packet-template.md](references/task-packet-template.md): Validated packet template.
- [references/bridge-contract.md](references/bridge-contract.md): Lifecycle states and transition rules.
- [references/quota-optimization.md](references/quota-optimization.md): Rules for agent allocation, batch audit, and quota saving.
- [scripts/bridge.py](scripts/bridge.py): Bridge runner script with OS locking and FIFO stream management.
