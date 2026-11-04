---
name: create-gpt-agy-gate
description: "Run a Codex PM and Antigravity implementation gate for scoped workspace tasks: create a task packet, dispatch one implementation round, audit real files, issue revisions, and approve only after quality gates pass."
---

# Create GPT AGY Gate

Use this skill for any scoped implementation, repair, migration, documentation, content, data, or automation task where Codex must coordinate Antigravity CLI and personally audit the result. The domain, workspace, files, tests, and acceptance criteria are supplied per task; do not assume a particular product or subject area.

## Roles

- Codex is PM and auditor. It owns scope, acceptance criteria, revision decisions, and final approval for any domain.
- Antigravity CLI is implementer and reporter. It edits only the assigned scope and never approves its own work.
- The bridge is a one-shot dispatcher. It calls `agy` once, records the response, and exits.

## Required operating model

1. Read the workspace `AGENTS.md`, the bridge `PROTOCOL.md` (the bridge's only local rule file), relevant roadmap/skill files, and current mailbox state.
2. Do not revive terminal tasks. Create one task packet with a unique `task_id`, `scope`, `acceptance_criteria`, `quality_gates`, `do_not_change`, `AUTOPILOT: false`, and `MAX_ROUNDS`.
3. Set the task to `queued` and run:

   `python3 .antigravity/agy-bridge/bridge.py`

   The current bridge is one-shot by default; `--once` remains a compatible explicit flag.

4. Keep the active Codex turn open while Antigravity runs. Read its response and inspect the actual working tree, not just the report.
5. If any gate fails, write a precise revision assignment naming the file, defect, required fix, and test evidence. Increment the round and run the bridge once again.
6. Stop early only when every gate passes. Set `approved` only after Codex verifies the files. If `MAX_ROUNDS` is reached first, set `stopped` and report the remaining defects.

### MAX_ROUNDS inheritance

- If the user does not specify a new `MAX_ROUNDS`, inherit the currently effective limit for the active workflow.
- If the user specifies a new limit, update the active task packet and every related assignment/revision record before dispatching the bridge.
- Do not dispatch while packet, generated prompt, and task log contain different limits.

Do not send a final response after merely creating the task or receiving the first Antigravity response. The active Codex turn must continue through audit and revisions. If the user asks to stop, stop immediately and mark the task `stopped`.

## Response-triggered handoff and quota discipline

- Treat the bridge process completion plus its `Antigravity → Codex` mailbox block as the only normal handoff signal. Do not poll `chat.md` while Antigravity is running.
- After handoff, inspect only the response, changed files/diff, focused risk samples, and consolidated quality checks. Do not reread unchanged course or workspace files.
- If the bridge exits without a response, perform one diagnostic check for timeout/launcher failure. Do not create repeated retries or duplicate packets without evidence that the prior process is dead.
- A mailbox response cannot wake a Codex session that has already ended. The live Codex turn must remain open for automatic audit/revision; otherwise a later user message must reopen the workflow.
- This handoff rule optimizes quota and latency; it does not authorize a background Codex daemon, watcher, or autonomous PM process.
- After dispatching a task, do not send a `final` status update or end the active turn merely because Antigravity is still working. Keep the live turn open through bridge response, audit, any consolidated revisions, and the terminal decision.
- End the turn only for `approved`, `stopped` at the configured round cap, an explicit user stop, or a real blocker requiring user input. Never describe an active task as finished or leave it at an ambiguous “waiting” conclusion.

## Assignment design

Keep task packets concise. Put task-specific scope, DoD, tests, and prohibitions in the packet; keep universal lifecycle and reporting rules in `PROTOCOL.md` instead of pasting them into every prompt. The bridge adds only a short wrapper and the packet itself. Require the four compact report fields: `Changed`, `Verified`, `Remaining`, `Decision`.

For a new domain, first identify the user's actual deliverable, source of truth, permitted paths, observable quality gates, and prohibited changes. Do not import examples, assumptions, or tests from another user's workspace.

## Audit requirements

Follow the audit and lifecycle rules in `PROTOCOL.md`. Audit real files and diff after each response, using machine checks plus focused risk samples; do not reread unchanged artifacts. Record only a concise audit or revision packet in `chat.md` when a measurable gate fails.

## Supporting references

- Read [references/task-packet-template.md](references/task-packet-template.md) when creating a new task.
- Read [references/audit-checklist.md](references/audit-checklist.md) before approving or stopping a task.
- Read [references/bridge-contract.md](references/bridge-contract.md) when modifying the bridge or diagnosing lifecycle behavior.
- Read [references/quota-optimization.md](references/quota-optimization.md) for rules on model selection, single-round execution, token-saving reports, and batch audits.
