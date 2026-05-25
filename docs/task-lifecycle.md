# Task Lifecycle

Every task in the swarm follows a defined lifecycle. This document specifies each stage, the transitions between stages, and the artifacts produced at each stage.

---

## Task Status States

```
PENDING → ACTIVE → DONE
           ↓
        BLOCKED → ESCALATED → (human resolves) → PENDING
           ↓
        FAILED → (retry if budget > 0) → ACTIVE
                                       → BLOCKED (budget exhausted)
```

---

## Stage Details

### PENDING

The task is in the task graph but has not been dispatched.

**Conditions for leaving PENDING:**
- All dependencies are DONE
- Agent is available
- No approval flag blocking dispatch

**Artifacts:** `state/tasks/<id>/brief.md`

---

### ACTIVE

The task has been dispatched to an agent and is being executed.

**Agent actions in ACTIVE:**
1. Read brief and plan
2. Execute using assigned skill
3. Write execution log
4. Mark output complete or flag a block

**Conditions for leaving ACTIVE:**
- Output complete → DONE (pending validation)
- Block encountered → BLOCKED
- Retry needed → FAILED

**Artifacts:** 
- `state/tasks/<id>/log.md`
- `state/tasks/<id>/outputs/`

---

### DONE

The task output has been validated and all acceptance criteria are met.

**Conditions for entering DONE:**
- All acceptance criteria verified
- Quality gate(s) for this task passed
- `state/tasks/<id>/validation.md` confirms pass

**Artifacts:**
- `state/tasks/<id>/validation.md` (status: DONE)
- `state/tasks/<id>/outputs/` (complete)

---

### BLOCKED

The task cannot proceed due to an external dependency, missing information, or approval requirement.

**Block reasons:**
- Dependency task not yet complete
- Required external resource unavailable
- Human approval required
- Ambiguous instruction that cannot be resolved

**Actions:**
1. Log block reason to `state/tasks/<id>/log.md`
2. Notify orchestrator
3. Do not retry — fix the block first

**Artifacts:**
- `state/tasks/<id>/status.md` (status: BLOCKED, reason: ...)

---

### FAILED

The task was executed but the output does not meet acceptance criteria or a validation gate failed.

**Actions:**
1. Log failure to `state/tasks/<id>/validation.md`
2. Decrement retry budget
3. If budget > 0: address specific failure, return to ACTIVE
4. If budget == 0: move to BLOCKED with reason "retry budget exhausted"

**Artifacts:**
- `state/tasks/<id>/validation.md` (status: FAILED, gate: ..., reason: ...)

---

### ESCALATED

The task is blocked and the orchestrator has routed it to human review.

**Conditions:** BLOCKED tasks that cannot be resolved by the swarm.

**Actions:**
1. Write `state/runs/<run-id>/approvals-pending.md`
2. Loop pauses on this task (continues with other tasks if possible)
3. Resume when human responds

---

## Task File Structure

```
state/tasks/<task-id>/
  brief.md          # Task specification (inputs, outputs, acceptance criteria)
  log.md            # Execution log (what happened)
  outputs/          # All task outputs
  validation.md     # Gate check results
  status.md         # Current status
  review.md         # Reviewer report (if reviewed)
  triage.md         # Bug triage (if debugging)
  red-team-report.md # Red team report (if activated)
```

---

## Task Brief Format

```yaml
# state/tasks/<id>/brief.md
task_id: T001
description: Implement JWT generation
primary_agent: coder
supporting_agents: [reviewer]
skill: code-implementation
inputs:
  - T000/outputs/jwt-schema.yaml
outputs:
  - src/auth/jwt.ts
  - state/tasks/T001/outputs/
acceptance_criteria:
  - generates signed JWT from user payload
  - validates expiry configuration
  - handles RS256 and HS256
dependencies: [T000]
retry_budget: 3
requires_approval: false
```

---

## Related Documents

- `docs/operating-model.md` — the swarm loop
- `docs/quality-gates.md` — gate definitions
- `AGENTS.md §6, §8, §9` — decomposition, execution, and validation protocols
