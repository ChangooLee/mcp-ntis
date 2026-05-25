# Convergence Model

This document defines when the swarm considers a run complete, stuck, or failed — and what to do in each case.

---

## What Is Convergence?

A swarm run **converges** when the task graph reaches a terminal state: all tasks are DONE, or all remaining tasks are permanently blocked. Convergence is detected by the orchestrator at the end of each cycle.

There are four convergence states:

| State | Meaning | Action |
|---|---|---|
| `COMPLETE` | All tasks DONE, all quality gates pass | Write summary, trigger reflection, hand off to operator |
| `PARTIAL` | Some tasks DONE, some permanently blocked | Write partial summary, surface blockers, hand off |
| `STUCK` | No progress in N consecutive cycles | Escalate to operator with diagnostic |
| `FAILED` | Stop condition hit (security, retry exhaustion, instruction conflict) | Hard stop, write stopped.md |

---

## Convergence Detection Algorithm

Run at the end of every orchestration cycle:

```
1. Count tasks by status:
   - DONE count
   - BLOCKED (approval-rejected or approval-timeout) count — these are permanent
   - ACTIVE count
   - PENDING count

2. If ACTIVE == 0 AND PENDING == 0:
   - If DONE > 0 AND permanent-BLOCKED == 0: state = COMPLETE
   - If DONE > 0 AND permanent-BLOCKED > 0: state = PARTIAL
   - If DONE == 0: state = FAILED (nothing completed)

3. If (ACTIVE + PENDING) > 0:
   - Check progress: did any task move to DONE this cycle?
   - If yes: run is still progressing → continue
   - If no progress in last 2 cycles: state = STUCK

4. If max_iterations reached: escalate regardless of state
```

---

## Complete Convergence

**Conditions:**
- All tasks in the task graph are in `DONE` status
- All universal quality gates pass
- All project-type-specific quality gates pass

**Actions:**
1. Write `state/runs/<run-id>/summary.md` (see format below)
2. Execute the `retrospective-and-reflection` skill
3. Execute the `memory-update` skill
4. Write `state/runs/<run-id>/convergence.md` with `state: COMPLETE`
5. Notify operator via `state/runs/<run-id>/approvals-pending.md` (handoff request)

---

## Partial Convergence

**Conditions:**
- At least one task is DONE
- At least one task is permanently blocked (`approval-rejected`, `approval-timeout`, or exhausted retry budget)
- No further progress is possible without operator intervention

**Actions:**
1. Write partial summary — list what was completed, what was blocked and why
2. Do not block on the blocked tasks — surface them clearly
3. Write `state/runs/<run-id>/convergence.md` with `state: PARTIAL`
4. Trigger reflection (same as COMPLETE, but note the partial state)
5. List recovery steps the operator must take to unblock

**Operator receives:**
- What was delivered
- What was not delivered and why
- Exact steps to resume (e.g., approve the blocked action, provide missing credentials)

---

## Stuck Detection

A run is **stuck** when it has not made progress for 2 consecutive cycles.

**Progress is defined as:** at least one task moved from non-DONE to DONE status.

### Stuck Triggers

| Trigger | Meaning |
|---|---|
| Same tasks blocked for 2 cycles | Systematic blocker, not task-specific |
| All active tasks waiting on the same dependency | Circular or chain dependency issue |
| All active tasks failing with the same error | Skill or environment failure |
| Orchestrator cannot assign any PENDING task | Routing or resource gap |

### Stuck Diagnosis

When stuck is detected, the orchestrator runs a diagnostic:

```
1. Which tasks are blocked? (list with block reasons)
2. Is there a common dependency? (detect fan-in)
3. Is there a circular dependency? (detect cycles in task graph)
4. Is there a missing skill or agent?
5. Is the orchestrator itself misrouting?
```

Write diagnostic to `state/runs/<run-id>/diagnostics.md`.

### Stuck Response

1. Write `state/runs/<run-id>/convergence.md` with `state: STUCK`
2. Escalate to operator with the diagnostic
3. Do not loop further — await operator guidance
4. If operator provides guidance: resume from the guidance, reset stuck counter

---

## Failed Convergence

A run **fails** when a hard stop condition is hit. See `AGENTS.md §15` for the complete list.

**Hard fail scenarios:**
- Retry budget exhausted on a critical task
- Security-sensitive operation detected
- Instruction conflict cannot be resolved
- max_iterations reached

**Actions:**
1. Write `state/runs/<run-id>/stopped.md` with the stop reason
2. Do not trigger reflection (state is too uncertain)
3. Write whatever partial outputs exist to `state/tasks/<id>/outputs/`
4. Notify operator immediately

---

## Run Summary Format

`state/runs/<run-id>/summary.md`:

```markdown
# Run Summary: <run-id>

## Convergence State: <COMPLETE | PARTIAL | STUCK | FAILED>

## Tasks Completed
- T001: <description> — DONE
- T002: <description> — DONE

## Tasks Blocked
- T003: <description> — BLOCKED (reason)

## Quality Gates
- [PASS] universal-completeness
- [PASS] universal-correctness
- [FAIL] sw-test-coverage (reason)

## Deliverables
<list of files/artifacts produced>

## Handoff Notes
<what the operator receives and next steps>

## Reflection
<link to state/reflections/<run-id>.md>
```

---

## Convergence File Format

`state/runs/<run-id>/convergence.md`:

```markdown
# Convergence: <run-id>

state: COMPLETE | PARTIAL | STUCK | FAILED
detected_at_cycle: <N>
timestamp: <ISO 8601>

tasks_done: <count>
tasks_blocked: <count>
tasks_pending: <count>

notes: |
  <brief explanation of convergence state>
```

---

## Progress Detection in Detail

### What Counts as Progress

| Event | Counts as Progress? |
|---|---|
| Task moves from ACTIVE → DONE | Yes |
| Task moves from PENDING → ACTIVE | Yes (partial credit) |
| Task moves from ACTIVE → BLOCKED | No (regression) |
| Escalation submitted | No (coordination, not output) |
| Quality gate passes on existing output | Yes |
| Memory or log updated | No (overhead, not output) |

### No-Progress Cycle

A cycle with no progress is logged in `state/runs/<run-id>/cycle-log.md` as:

```
Cycle N: no-progress (stuck-counter: 1 of 2)
Reason: <all active tasks blocked waiting on T003 approval>
```

After 2 no-progress cycles: escalate.

---

## Max Iterations Handling

When `run.max_iterations` (default: 10) is reached:

1. Check convergence state: if COMPLETE, proceed normally
2. If not COMPLETE: write `stopped.md` with reason `max-iterations-reached`
3. List all remaining work (PENDING + ACTIVE tasks) in `stopped.md`
4. Trigger reflection with note that run was cut short
5. Update operator: swarm has delivered what it could, remaining work is listed

The operator can extend max_iterations and resume by creating a new run with the remaining task graph.

---

## Convergence vs. Escalation

| Situation | Action |
|---|---|
| Run is done but quality gate fails | Retry gate (up to gate retry budget); then converge PARTIAL |
| Run is stuck but retry budget remains | Use remaining retries before calling stuck |
| Run is stuck and retry budget exhausted | Stuck is confirmed; escalate |
| All tasks done, no quality gates defined | Converge COMPLETE with a note that gates were not defined |
| Operator manually stops the run | Treat as max-iterations; write stopped.md |

---

## Related Documents

- `AGENTS.md §15, §16` — stop conditions, retry budgets
- `docs/escalation-model.md` — what happens when runs escalate
- `docs/runbook-recovery.md` — how to recover a stuck or failed run
- `docs/operating-model.md` — the swarm loop and cycles
