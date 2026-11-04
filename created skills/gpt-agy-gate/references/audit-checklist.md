# Audit Checklist

## Scope and state

- Confirm the task ID, status, round, and allowed path.
- Inspect the working tree and actual file contents.
- Confirm no commit, push, delete, rename, or out-of-scope edits occurred.

## Deliverable and content

- Check every acceptance criterion against evidence in the files.
- Distinguish implemented content from specifications, placeholders, and claims in reports.
- Check consistency across whatever artifacts the task defines: files, code, data, documents, UI, metadata, records, or external outputs.

## Technical quality

- Parse all relevant HTML or structured files.
- Check local links and asset paths.
- Run language or JavaScript syntax checks.
- Test the task's important behaviors and failure/no-data fallbacks.
- Check domain-specific usability, compatibility, safety, accessibility, reproducibility, or performance requirements when relevant.
- Scan for the task's forbidden patterns, secrets, and accidental scope expansion.

## Decision

- `approved`: every gate has evidence and no required work remains.
- `revision`: list exact file, defect, fix, and test required.
- `stopped`: only after `MAX_ROUNDS` or an explicit user stop; report remaining work and blockers.
