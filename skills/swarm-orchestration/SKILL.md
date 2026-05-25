---
id: swarm-orchestration
title: Swarm Orchestration
version: 1.0
purpose: Coordinate a multi-agent swarm run from start to finish: initialize the loop, sequence agents, handle escalations, enforce stop conditions, and produce the final run summary.
when_to_use:
  - At the start of every swarm run
  - When the orchestrator agent needs to re-sequence after a failure
  - When an escalation arrives and the loop must adapt
when_not_to_use:
  - For single-agent, single-task work that doesn't need coordination
  - Within a specific task execution (this skill manages the loop, not tasks)
required_inputs:
  - state/runs/<run-id>/context.md
  - state/runs/<run-id>/task-graph.md
  - state/runs/<run-id>/routing.md
outputs:
  - state/runs/<run-id>/manifest.yaml (updated each cycle)
  - state/runs/<run-id>/cycle-log.md (one entry per iteration)
  - state/runs/<run-id>/summary.md (final, on completion or stop)
related_docs:
  - docs/operating-model.md
  - docs/task-lifecycle.md
  - AGENTS.md §7, §15, §16
escalation: If the run reaches max iterations without completing, stop the loop, write a stop reason, and request human review of remaining work.
---

# Skill: Swarm Orchestration

## Purpose

Run the swarm loop: sequence agents, monitor iteration budget, handle failures, enforce stop conditions, and produce a coherent summary.

## Workflow

The orchestration loop runs in cycles. Each cycle:

```
1. Check stop conditions
2. Identify the next ready task(s) (dependencies satisfied, not blocked)
3. Dispatch task to primary agent
4. Wait for task completion or block signal
5. Validate task output
6. Handle failures (retry or escalate)
7. Update run manifest
8. Log cycle
9. Increment iteration counter
10. Loop or exit
```

### Step 1 — Initialize loop

1. Confirm context, task graph, and routing are ready
2. Initialize `state/runs/<run-id>/cycle-log.md`
3. Set `current_iteration: 0` in manifest

### Step 2 — Each cycle

**Check stop conditions (fail fast):**
- `current_iteration >= max_iterations` → stop with reason
- Any task has exhausted retry budget → escalate
- Two consecutive cycles blocked for same reason → escalate
- Security-sensitive action detected → pause and request approval

**Find ready tasks:**
- Status is `PENDING`
- All dependencies have status `DONE`
- Not marked `requires_approval: true` (unless approval received)

**Dispatch:**
- Call the primary agent with the task brief
- Record: `cycle N → task T_id → agent X → started`

**On completion:**
- Validate against acceptance criteria
- If pass → mark DONE
- If fail → retry or escalate (per retry budget)

**Log cycle:**
```markdown
## Cycle <n>
Tasks dispatched: T001, T003
Tasks completed: T001
Tasks blocked: T003 (reason: missing env variable)
Escalations: none
Iteration budget remaining: <max - n>
```

### Step 3 — Handle escalations

When an escalation arrives:
1. Log to `state/runs/<run-id>/escalations.md`
2. Determine if it's blockable (missing info, approval needed) or fatal (stop condition)
3. If blockable: pause task, try next ready task
4. If fatal: stop loop, write stop reason, request human review

### Step 4 — Detect convergence

The loop converges when:
- All tasks are DONE → complete the run
- No tasks are ready and some are blocked → stuck state → escalate

### Step 5 — Complete the run

On convergence or stop:
1. Update manifest: `status: completed | stopped | blocked`
2. Trigger retrospective skill
3. Trigger memory update skill
4. Write final summary

## Do

- Enforce stop conditions without exception
- Log every cycle with specific task and agent details
- Handle partial completion gracefully (some DONE, some BLOCKED)

## Don't

- Don't continue past a stop condition
- Don't dispatch tasks with unmet dependencies
- Don't mark the run complete when tasks are blocked — mark it stopped
