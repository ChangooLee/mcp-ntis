---
id: goal-decomposition
title: Goal Decomposition
version: 1.0
purpose: Break a high-level project goal into a concrete, executable task graph with clear dependencies, agent assignments, and acceptance criteria.
when_to_use:
  - After project intake, when goals are clear but work is not yet structured
  - When a large task needs to be broken down further
  - When the critical path needs to be identified
when_not_to_use:
  - For trivial single-step tasks
  - Before project intake is complete
  - When an existing task graph already covers the goal
required_inputs:
  - state/runs/<run-id>/context.md (project context from intake)
  - README.md (for goal inference if context is incomplete)
outputs:
  - state/tasks/ (individual task files)
  - state/runs/<run-id>/task-graph.md (the full task graph)
  - state/runs/<run-id>/critical-path.md (critical path identification)
related_docs:
  - docs/task-lifecycle.md
  - docs/agent-matrix.md
  - AGENTS.md §6
escalation: If decomposition reveals that the project scope exceeds the run's iteration budget, escalate to the orchestrator for scope adjustment before proceeding.
---

# Skill: Goal Decomposition

## Purpose

Produce a task graph where every leaf task is: independently executable, validatable, and assignable to a specific agent.

## Workflow

### Step 1 — Identify top-level goals

From the project context, list 3–7 top-level goals:
- Each must be an outcome, not an activity
- Good: "Working authentication API with JWT"
- Bad: "Write the auth code"

### Step 2 — Decompose each goal

For each goal, break it into subtasks (max 4 levels deep):
```
Goal: Working authentication API with JWT
  └─ Task T001: Design auth module architecture
     └─ Task T001a: Define JWT payload schema
     └─ Task T001b: Define session lifecycle
  └─ Task T002: Implement JWT generation
  └─ Task T003: Implement JWT validation middleware
  └─ Task T004: Write auth unit tests
  └─ Task T005: Write auth integration tests
  └─ Task T006: Document auth API endpoints
```

### Step 3 — Assign agents

For each leaf task, assign the primary agent using `docs/agent-matrix.md`.

### Step 4 — Define acceptance criteria

For each leaf task:
```yaml
task_id: T002
description: Implement JWT generation
agent: coder
skill: code-implementation
inputs:
  - T001a output (JWT schema)
  - T001b output (session lifecycle doc)
outputs:
  - src/auth/jwt.ts
  - state/tasks/T002/outputs/
acceptance_criteria:
  - generates signed JWT from user payload
  - validates expiry configuration
  - handles RS256 and HS256 algorithm selection
dependencies: [T001a, T001b]
retry_budget: 3
requires_approval: false
```

### Step 5 — Identify critical path

The critical path is the longest chain of dependent tasks. Optimize it:
- Can any tasks on the critical path be parallelized?
- Are any blocking dependencies avoidable?

### Step 6 — Write task graph

Write `state/runs/<run-id>/task-graph.md` with:
- Full list of tasks
- Dependency graph (as indented list or ASCII diagram)
- Critical path highlighted
- Total estimated task count vs. iteration budget

### Step 7 — Create individual task files

For each task: `state/tasks/<id>/brief.md` with the YAML from Step 4.

## Do

- Make every leaf task independently executable
- Define acceptance criteria in terms of observable outputs
- Flag tasks that need human approval in the task brief

## Don't

- Don't create tasks so granular they take < 5 minutes (batch them)
- Don't create tasks without acceptance criteria
- Don't nest more than 4 levels — reconsider scope
- Don't assign multiple primary agents to one task (supporting agents are fine)
