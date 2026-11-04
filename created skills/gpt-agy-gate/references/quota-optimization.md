# Quota and Token Optimization Protocol

Use this protocol to minimize token consumption, round-trips, and quota usage across any AI agent collaboration.

## Roles

- **User**: Defines high-level objectives, boundary constraints, and quality standards.
- **PM / Auditor (Codex)**: Owns scope, acceptance criteria, single-pass batch audit, and terminal approval. Does not write code when the implementer can do it.
- **Implementer (Antigravity CLI)**: Reads files, plans internally, executes full scope in one shot, verifies via automated tests, and reports concisely. Never self-approves.

## Cheapest Default Flow (One-Shot + Max 1 Revision)

```text
User Request
  -> PM writes complete, self-contained spec
  -> Implementer executes entire scope in one shot
  -> Implementer runs automated verification
  -> PM performs 3-layer batch audit
  -> Pass: Approve immediately
  -> Fail: Issue exactly ONE consolidated revision packet
  -> PM audits revision
  -> Stop
```

Target: Exactly 1 primary implementation round + at most 1 revision round. No piecemeal chatting or micro-rounds.

## Complete Spec Requirements

Every task packet dispatched by PM must include:
1. Final objective.
2. Explicit file/directory scope.
3. Prohibited actions (`do_not_change`).
4. Measurable Definition of Done.
5. Concrete automated tests.
6. Execution mandate: self-decompose internally, no mid-flight status reports, no plan-only / audit-only responses, complete maximum scope before returning.
7. Concise report format (`Changed`, `Verified`, `Remaining`, `Decision`).
8. `MAX_ROUNDS: 2`.

## Agent and Model Allocation

- **Agent Count**:
  - Small task (1 bug, 1 localized area): 1 agent.
  - Medium task (multiple files in same system): 1 primary agent with internal decomposition.
  - Large task (fully disjoint file boundaries): 2-4 parallel agents with non-overlapping file sets. PM audits once after all finish.
  - Prohibition: Never assign multiple agents to edit shared CSS, configs, lockfiles, schemas, or the same file.
- **Model Selection**:
  - Mechanical work (renames, linting, formatting, link checks, mechanical migrations): Light model.
  - Debugging, refactoring, standard features: Workhorse model.
  - Architecture, security, high-risk domain data (finance, legal, medical), deep research: Strong model. Never use light models to hallucinate domain knowledge or make architectural decisions.

## 3-Layer Minimum-Sufficient Audit

Do not manually inspect every file. Audit using three layers:
1. **Machine Layer**: Automated build, test, lint, type check, link/asset checker, secret/placeholder scanner.
2. **Diff Layer**: Verify changed files stay strictly within scope; scan for copy-paste, hard-coding, or placeholders.
3. **Risk Sample Layer**: Deeply inspect high-risk files only (entrypoints, complex business logic, files reported broken by user). Do not review 100 files when tests and risk samples provide sufficient proof.

## Revision Criteria

Issue a revision packet ONLY when:
- Automated tests fail.
- Acceptance criteria are unmet.
- Agent touched zero files or missed implementation.
- Report contradicts actual git diff.
- Changes exceed authorized scope.
- User directly observes a functional or UX bug.
- A genuine blocker requires a decision.
Never issue a revision simply to "double check". If criteria pass, approve immediately.

## Token-Saving Report Format

The implementer must omit greetings, restated requirements, lengthy plans, internal thoughts, and redundant code snippets. Report strictly:

```text
Changed:
- <file>: <summary of real change>

Verified:
- <test command>: <concrete result>

Remaining:
- none / <concrete blocker>

Decision:
- none / <choice required from PM or User>
```
