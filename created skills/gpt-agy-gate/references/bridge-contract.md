# Bridge Contract

The bridge is a domain-neutral one-shot runner, not an autonomous auditor.

```text
queued -> bridge.py (one shot) -> running -> agy response -> waiting-review
```

Codex live performs the audit. It writes either a revision assignment or the terminal `approved` decision, then runs the bridge once for the next round when allowed. The bridge must not call `codex exec`, auto-approve, re-queue indefinitely, run as a background daemon, or wake a closed chat session. The implementation details and quality gates come entirely from the current user's task packet.

The active Codex turn must remain open while the task is being coordinated. A final response is sent only after approval, stop, or a real blocker.
