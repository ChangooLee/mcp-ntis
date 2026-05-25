---
id: code-implementation
title: Code Implementation
version: 1.0
purpose: Implement code changes that meet the task's acceptance criteria, following existing conventions, without introducing regressions.
when_to_use:
  - Implementing a new feature or module
  - Fixing a specific bug with a known root cause
  - Refactoring a bounded section of code
when_not_to_use:
  - Without a task brief and acceptance criteria
  - Without a repo recon (for existing projects)
  - When the approach is undecided — plan first
  - For test-only tasks (use test-authoring skill)
required_inputs:
  - state/tasks/<id>/brief.md (task brief + acceptance criteria)
  - .cursor/plans/<task-id>-plan.md (implementation plan)
  - state/runs/<run-id>/recon.md (for existing projects)
outputs:
  - Modified or new source files
  - state/tasks/<id>/outputs/ (summary of changes)
  - state/tasks/<id>/log.md (execution log)
related_docs:
  - docs/architecture.md
  - AGENTS.md §8
escalation: If a blocking dependency is discovered mid-implementation, stop and notify the orchestrator. Do not workaround dependencies silently.
---

# Skill: Code Implementation

## Purpose

Produce working, tested, convention-compliant code that passes the task's acceptance criteria.

## Workflow

### Step 1 — Review plan and brief

1. Read `state/tasks/<id>/brief.md` — acceptance criteria are the contract
2. Read `.cursor/plans/<task-id>-plan.md` — follow the steps, don't improvise
3. If the plan is missing: create it first (use implementation-planning skill)

### Step 2 — Identify files to create or modify

List:
- Files to create (new)
- Files to modify (existing — read them first)
- Files to leave alone

### Step 3 — Read before writing

For every file to be modified:
1. Read the full file
2. Understand existing patterns and conventions
3. Identify the minimal change needed

### Step 4 — Implement

Follow this order:
1. Data structures / types / schemas first
2. Core logic second
3. Integration / wiring third
4. Error handling fourth
5. Logging / observability last

**Coding principles:**
- Match existing naming conventions exactly
- Match existing import style
- Do not add features beyond the task scope
- Prefer simple, readable code over clever code
- Add comments only where the logic is non-obvious

### Step 5 — Self-review

Before marking complete:
- Does the code do what the acceptance criteria require?
- Does it follow existing conventions?
- Are there any obvious bugs or edge cases?
- Is there any dead code or commented-out code to remove?
- Are error cases handled?

### Step 6 — Write execution log

`state/tasks/<id>/log.md`:
```markdown
# Execution Log: <task-id>
Date: <date>
Files modified:
  - <file>: <what changed>
Files created:
  - <file>: <purpose>
Approach taken: <brief>
Deviations from plan: <any? why?>
Known limitations: <any?>
```

## Do

- Read existing code before modifying it
- Match existing conventions
- Write the minimal change that satisfies acceptance criteria
- Log what you changed and why

## Don't

- Don't add features not in the task scope
- Don't change unrelated code while implementing a feature
- Don't skip reading existing code — wrong assumptions cause regressions
- Don't leave TODO comments without a corresponding task
- Don't write code without running tests (if tests exist)
