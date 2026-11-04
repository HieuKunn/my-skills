# Task Packet Template

```text
<!-- TASK id=<unique-id> status=queued from=codex -->
AUTOPILOT: false
MAX_ROUNDS: <positive integer>

## Scope
<exact workspace, files, inputs, and outputs allowed for this user's domain>

## Acceptance criteria
- <observable requirement specific to this user's deliverable>

## Quality gates
- <reproducible test, inspection, review, or acceptance check>

## Do not change
- No commit, push, delete, rename, or out-of-scope edits unless explicitly authorized.

## Antigravity completion rule
- Implement and report only.
- Do not self-approve or claim completion while any requirement or gate is unverified.
- Report files read/changed, changes, unfinished work, blockers, risks, tests, and decisions needed.

<!-- END TASK -->
```

Keep one active task packet. Preserve old terminal tasks as history unless the user explicitly requests mailbox cleanup.

The template is domain-neutral. Replace every placeholder with the user's actual project language and constraints; never copy course, web, code, or finance assumptions into an unrelated task.
