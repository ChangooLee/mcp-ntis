---
id: implementation-planning
title: Implementation Planning
version: 1.0
purpose: Create a concrete, step-by-step implementation plan for a specific task before execution begins.
when_to_use:
  - For any task > 2 hours or touching > 3 files
  - Before implementing any public interface (API, schema, CLI)
  - For tasks that have architectural implications
when_not_to_use:
  - For trivial tasks (< 30 min, 1 file, no interface changes)
  - When a plan already exists for this task
required_inputs:
  - state/tasks/<id>/brief.md (task brief with acceptance criteria)
  - state/runs/<run-id>/recon.md (repo recon, if applicable)
outputs:
  - .cursor/plans/<task-id>-plan.md (implementation plan)
related_docs:
  - docs/architecture.md
  - AGENTS.md §5
escalation: If implementation approach is ambiguous between two valid alternatives with significant tradeoffs, surface both to the orchestrator or operator before committing to one.
---

# Skill: Implementation Planning

## Purpose

Produce a plan that another agent can execute without having to make major architectural decisions mid-task.

## Workflow

### Step 1 — Understand the task

Read the task brief and acceptance criteria. Restate the goal in one sentence.

### Step 2 — Identify constraints

From the repo recon and task brief:
- Tech stack constraints
- Existing patterns to follow
- Interfaces to not break
- External dependencies

### Step 3 — Enumerate approaches

List 1–3 valid approaches. For each:
- Brief description
- Pros
- Cons
- Risk

### Step 4 — Select approach

Select the approach that:
- Minimizes risk to existing behavior
- Best follows existing conventions
- Is most testable
- Is reversible if wrong

### Step 5 — Write implementation steps

Break the selected approach into ordered steps:
```
1. Create <file> with <purpose>
2. Implement <function> that <does>
3. Wire into <existing integration point>
4. Add tests for <cases>
5. Update <doc> with <info>
```

Each step must be:
- Independently executable
- Reversible if wrong
- Verifiable when done

### Step 6 — Identify risks

List specific risks and mitigations:
- "If X breaks, roll back by Y"
- "Edge case Z needs explicit test"

### Step 7 — Write the plan file

`.cursor/plans/<task-id>-plan.md`:
```markdown
# Plan: <task-id> — <short title>
Date: <date>
Agent: <assigned agent>
Goal: <one sentence>
Approach: <selected approach name>
Constraints:
  -
Steps:
  1.
  2.
Risks:
  -
Definition of done:
  - <from acceptance criteria>
```

## Examples

**Good plan step:**
"Implement `validateToken(token: string): Promise<JWTPayload>` in `src/auth/jwt.ts`. Follow the existing `verifySignature` pattern in `src/crypto/`. Handle token expiry as a thrown `TokenExpiredError` (not a return value). Add unit test in `src/auth/jwt.test.ts`."

**Bad plan step:**
"Write the token validation code."

## Do

- Write steps specific enough that a different agent could execute them
- Reference existing patterns and files explicitly
- Flag anything that might need human review

## Don't

- Don't write vague steps like "implement the feature"
- Don't skip the alternatives section for significant decisions
- Don't plan more than 10 steps — split into multiple tasks instead
