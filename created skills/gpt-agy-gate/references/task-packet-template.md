# Task Packet Template

```text
<!-- TASK id=TASK-001 status=queued created=2026-11-09T16:00:00+08:00 -->
TASK_VERSION: 1
PARENT_TASK: none
ROUND: 1
MAX_ROUNDS: 2
TIMEOUT_SECONDS: 7200
MAX_SUBAGENT_CALLS: 0
MAX_PARALLEL_AGENTS: 1
ACCEPTANCE_MODE: delegated

Objective:
[Final outcome / deliverable]

Context:
[Essential background, files, links]

Scope:
[Exact workspace, files, inputs, and outputs allowed]

Do:
[Concrete actions to perform]

Do not:
[Prohibited actions: no rename/delete/commit/push or out-of-scope edits]

Definition of Done:
[Measurable and observable acceptance criteria]

Verification:
[Concrete automated commands, tests, or reproducible checks]

Agent policy:
- Self-decompose internally if needed.
- No mid-flight status reports or plan-only responses.
- Implement full scope before returning.
- Subagents permitted only up to MAX_SUBAGENT_CALLS.

Report format:
Changed:
- <file: exact change>

Verified:
- <command: result and exit code>

Evidence:
- <artifact or proof output>

Remaining:
- <none or specific blocker>

Decision:
- <none or explicit choice needed from Codex/User>
<!-- END TASK -->
```

## Mailbox and Stream Rules

- `chat.md` holds a maximum of 3 task streams (FIFO). Older streams are automatically pruned when a 4th root task is added.
- Revision packets must specify `PARENT_TASK: <root-task-id>` and increment `ROUND`. Revisions share the parent stream slot.
- `ACCEPTANCE_MODE`:
  - `delegated`: Codex live approves after successful verification.
  - `user_required`: Codex marks `verified`; User provides final approval.
- Agent completion rules: Implement and report only. Never self-approve.
