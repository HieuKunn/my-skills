# Bridge Contract and Lifecycle

The bridge is a strictly controlled one-shot attempt runner, not an autonomous auditor or background daemon.

## Lifecycle States

```text
queued → running → waiting-review → approved
                         ├────────→ verified (user_required)
                         ├────────→ rejected → queued (new revision)
                         ├────────→ blocked (timeout / error)
                         └────────→ stopped (cap exhausted / manual stop)
```

## Protocol Guardrails

- Bridge executes one attempt per run (`bridge.py` or `bridge.py --once`).
- Bridge applies OS-level file lock (`.bridge.lock`) to prevent concurrent modifications to `chat.md`.
- Mailbox maintains up to 3 task streams using FIFO: when a 4th root task packet arrives, the oldest stream (including its tasks, revisions, and messages) is deleted.
- Codex live performs the 3-layer audit (machine checks, diff/scope check, risk sample).
- When audit passes:
  - If `ACCEPTANCE_MODE: delegated` → marks `approved`.
  - If `ACCEPTANCE_MODE: user_required` → marks `verified`, awaiting User confirmation.
- When audit fails:
  - Writes revision packet incrementing `ROUND`, pointing to `PARENT_TASK`, and re-queues until `MAX_ROUNDS` is reached.
- If rounds are exhausted without passing, state moves to `stopped` with `MAX_ROUNDS_EXHAUSTED`.
