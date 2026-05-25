---
id: task-routing
title: Task Routing
version: 1.0
purpose: Assign each task in the task graph to the correct primary and supporting agents, and confirm required skills are available.
when_to_use:
  - After goal decomposition produces a task graph
  - When the orchestrator needs to re-route a blocked or failed task
when_not_to_use:
  - Before a task graph exists
  - For trivial single-agent tasks where routing is obvious
required_inputs:
  - state/runs/<run-id>/task-graph.md
  - docs/agent-matrix.md
  - docs/project-types.md
outputs:
  - state/runs/<run-id>/routing.md (routing decisions with reasoning)
related_docs:
  - docs/agent-matrix.md
  - docs/operating-model.md
  - AGENTS.md §7
escalation: If no agent in the current team is qualified for a task, escalate to the orchestrator. Do not leave tasks unrouted.
---

# Skill: Task Routing

## Purpose

Produce a routing manifest that assigns every task to an agent with reasoning, so execution can proceed without ambiguity.

## Workflow

### Step 1 — Load routing tables

Read:
- `docs/agent-matrix.md` — task type to agent mapping
- `docs/project-types.md` — project-type-specific agent team
- Activated agent team from `state/runs/<run-id>/context.md`

### Step 2 — Route each task

For each task in the task graph:
1. Identify the task type (code, test, doc, research, review, etc.)
2. Look up the primary agent
3. Identify supporting agents if needed
4. Confirm the primary agent's skill list covers the task
5. If no match: flag as unrouted and escalate

### Step 3 — Check for routing conflicts

- Multiple tasks require the same agent sequentially → reorder if dependencies allow
- Multiple tasks require the same agent in parallel → split workload or serialize
- A task has no available agent → escalate

### Step 4 — Write routing manifest

`state/runs/<run-id>/routing.md`:
```markdown
# Routing: <run-id>

| Task ID | Description | Primary Agent | Supporting | Skill | Notes |
|---|---|---|---|---|---|
| T001 | Design auth architecture | architect | planner | implementation-planning | |
| T002 | Implement JWT generation | coder | reviewer | code-implementation | depends T001 |
| T003 | Write JWT tests | tester | coder | test-authoring | depends T002 |
| T004 | Document auth API | documenter | | doc-authoring | depends T002 |
```

### Step 5 — Update task briefs

For each task: add the routing decision to `state/tasks/<id>/brief.md`:
```yaml
primary_agent: coder
supporting_agents: [reviewer]
skill: code-implementation
```

## Do

- Assign every task to exactly one primary agent
- Verify the agent's skill list before routing
- Record why a routing decision was made (not just what)

## Don't

- Don't route tasks to agents without the required skills
- Don't leave tasks unrouted — escalate instead
- Don't route the orchestrator as primary on execution tasks (it coordinates, not executes)
