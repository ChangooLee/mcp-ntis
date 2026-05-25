---
id: bug-triage
title: Bug Triage
version: 1.0
purpose: Identify the root cause of a bug, assess severity and scope, and produce a structured fix brief.
when_to_use:
  - When a bug report or failing test is the starting point
  - When unexpected behavior is observed during verification
  - Before fixing any non-trivial bug (> 30 min to fix)
when_not_to_use:
  - For typos or trivially obvious one-line fixes
  - When the root cause is already definitively known
required_inputs:
  - Bug description or failing test output
  - Access to the relevant source files
  - state/runs/<run-id>/recon.md (if available)
outputs:
  - state/tasks/<id>/triage.md (structured triage report)
  - state/tasks/<id>/brief.md (updated with root cause and fix approach)
related_docs:
  - docs/operating-model.md
  - AGENTS.md §9
escalation: If the root cause requires a change to a foundational module that would affect > 5 other modules, escalate to the architect before fixing.
---

# Skill: Bug Triage

## Purpose

Produce a triage report that definitively identifies the root cause and proposes a targeted fix — not a workaround.

## Workflow

### Step 1 — Reproduce the bug

1. Read the bug description / failing test
2. Identify the minimal reproduction path
3. Confirm: can it be reproduced deterministically?
4. If not deterministic: classify as flaky (different triage path)

### Step 2 — Isolate the failing component

Work inward from the symptom:
- What is the observed behavior?
- What is the expected behavior?
- What is the last point in the call stack where behavior was correct?

### Step 3 — Identify root cause

Root cause categories:
| Category | Description |
|---|---|
| Logic error | Wrong conditional, off-by-one, wrong algorithm |
| Missing guard | Null/undefined not handled, empty input not handled |
| Race condition | Async ordering issue, shared mutable state |
| Integration mismatch | Two components with incompatible contracts |
| Config/env issue | Missing or wrong configuration value |
| Dependency bug | Bug in upstream library (verify before classifying) |

### Step 4 — Assess scope

- How many callers are affected?
- Does a fix require a breaking interface change?
- Are there other places in the codebase with the same pattern?

### Step 5 — Propose fix

Write a specific, targeted fix:
- What to change (file, line, function)
- What the change is
- Why it fixes the root cause
- What tests to add to prevent regression

### Step 6 — Write triage report

`state/tasks/<id>/triage.md`:
```markdown
# Triage Report: <task-id>
Date: <date>
Bug: <description>
Severity: critical | high | medium | low
Root cause: <specific description>
Root cause category: <from table above>
Scope: <files/modules affected>
Fix approach: <specific change>
Regression test needed: yes | no
Escalation needed: yes (<reason>) | no
```

## Do

- Find the root cause, not just the symptom
- Propose a targeted fix, not a broad defensive rewrite
- Always propose a regression test

## Don't

- Don't fix the symptom without understanding the cause
- Don't add broad defensive code to mask a bug
- Don't classify a bug as "dependency bug" without verifying the dependency actually has the bug
- Don't close a triage without a proposed fix approach
