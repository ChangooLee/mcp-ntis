# Runbook: Recovery from Failures

This runbook covers common failure scenarios and how to recover from them.

---

## Scenario 1: Swarm Stopped — Max Iterations Reached

**Symptom:** `state/runs/<run-id>/stopped.md` exists with reason "max iterations reached"

**Diagnosis:**
```bash
cat state/runs/<run-id>/stopped.md
cat state/runs/<run-id>/manifest.yaml  # check tasks_done vs tasks_total
cat state/runs/<run-id>/cycle-log.md   # last few cycles
```

**Recovery:**
1. Review the summary — what was completed
2. Review blocked tasks — why were they blocked?
3. Fix the root cause of any blocks (missing info, wrong scope, external dependency)
4. Optionally increase `max_iterations` in AGENTS.md for the next run
5. Start a new run: `bash scripts/run_swarm_cycle.sh`
   - The swarm will detect prior state and resume from where it stopped

---

## Scenario 2: Task Blocked — Human Approval Required

**Symptom:** `state/runs/<run-id>/approvals-pending.md` exists

**Diagnosis:**
```bash
cat state/runs/<run-id>/approvals-pending.md
```

**Recovery:**
1. Read the approval request — what action is needed and why
2. Decide: approve or reject
3. If approving:
   - Mark the file: add `approved: true` and `approved_by: <your-name>`
   - Run a new swarm cycle: `bash scripts/run_swarm_cycle.sh`
4. If rejecting:
   - Add `approved: false` and `reason: <why rejected>`
   - Update `state/memory/project.md` with new constraints
   - Run a new swarm cycle with revised instructions

---

## Scenario 3: Memory Conflict

**Symptom:** Project memory (`state/memory/project.md`) says X but the repo actually has Y

**Diagnosis:**
Compare memory to reality:
```bash
cat state/memory/project.md
ls state/tasks/*/status.md
```

**Recovery:**
1. Trust the current repo state, not the memory
2. Update `state/memory/project.md` to reflect reality
3. Log the correction in `state/reflections/` as a one-line note
4. If the conflict is systematic: check if `memory-update` skill was skipped in prior runs

---

## Scenario 4: Task Failed — Retry Budget Exhausted

**Symptom:** `state/tasks/<id>/status.md` shows BLOCKED with reason "retry budget exhausted"

**Diagnosis:**
```bash
cat state/tasks/<id>/validation.md  # what failed each time
cat state/tasks/<id>/log.md         # what was attempted
```

**Recovery:**
1. Read the specific validation failure — what acceptance criterion was not met?
2. Options:
   - **Revise acceptance criteria** if they were wrong (update task brief, restart task)
   - **Provide missing info** the task needed (update README or task brief)
   - **Change approach** if the implementation approach was wrong
   - **Reset retry budget** in the task brief (`retry_budget: 3`)
3. Reset task status: delete `state/tasks/<id>/status.md`
4. Run a new swarm cycle

---

## Scenario 5: Swarm Stuck in Loop

**Symptom:** cycle-log.md shows same task being retried repeatedly with same failure

**Diagnosis:**
```bash
tail -50 state/runs/<run-id>/cycle-log.md
cat state/tasks/<stuck-id>/validation.md
```

**Session-level diagnosis (if `agent-sessions` is installed):**
```bash
# Find sessions from this project today
agent-sessions -d $(pwd) -D 1

# Dump the stuck agent's session for raw transcript
agent-sessions dump <session-id>

# Search for the specific error pattern across all recent sessions
agent-sessions -e -s "retry budget" -D 1
```

**Recovery:**
1. Identify the specific failure reason in validation.md (or session transcript)
2. Stop the current run manually (the swarm should have caught this — file a retrospective note)
3. Fix the root cause
4. Reset the stuck task
5. Increase stuck-task detection sensitivity in AGENTS.md if this is a pattern

---

## Scenario 6: Incorrect Project Type Selected

**Symptom:** Wrong agent team is active; quality gates don't match the project

**Diagnosis:**
```bash
cat state/runs/<run-id>/context.md  # check project_type
```

**Recovery:**
1. Add `project_type: "<correct-type>"` explicitly to AGENTS.md
2. Clear the current run state (or note it as invalid)
3. Start a new run: `bash scripts/run_swarm_cycle.sh`

---

## Scenario 7: Quality Gate Failing Repeatedly

**Symptom:** Gate X keeps failing even after retries

**Diagnosis:**
```bash
cat state/runs/<run-id>/evaluation-report.md
# Identify which gate, which evidence is missing or wrong
```

**Recovery:**
1. Is the gate criteria correct for this project? If not: update gate config
2. Is the evidence missing? If so: add a task to produce it
3. Is the implementation genuinely broken? If so: route back to coder/researcher
4. If the gate is systematically misconfigured: update `docs/quality-gates.md` and log in `docs/decisions/`

---

## Scenario 8: Agent Produces Consistently Wrong Output

**Symptom:** A specific agent consistently fails its tasks

**Recovery:**
1. Read the agent's `agents/<name>.md` — is the scope correct?
2. Read the task briefs — are they providing the right inputs?
3. Check `state/reflections/` — is this a known pattern?
4. If `agent-sessions` is installed, search for prior instances:
   ```bash
   agent-sessions -e -s "<agent name or task keyword>" -D 30
   agent-sessions dump <prior-session-id>   # review what went wrong before
   ```
5. If skill issue: update the relevant `skills/<name>/SKILL.md`
6. If agent definition issue: propose update to `agents/<name>.md`
7. If instruction issue: engage the `prompt-engineer` agent

---

## Emergency Reset

If the swarm state is completely corrupted:

```bash
# Preserve memory and reflections
cp -r state/memory /tmp/memory-backup
cp -r state/reflections /tmp/reflections-backup

# Clear runtime state
rm -rf state/tasks state/runs state/artifacts

# Restore preserved state
cp -r /tmp/memory-backup state/memory
cp -r /tmp/reflections-backup state/reflections

# Start fresh run
bash scripts/bootstrap.sh
bash scripts/run_swarm_cycle.sh
```

---

## Related Documents

- `docs/operating-model.md` — the swarm loop
- `docs/task-lifecycle.md` — task status transitions
- `docs/memory-model.md` — memory layers and conflict resolution
- `AGENTS.md §15, §16, §17` — stop conditions, retry budgets, escalation
- `AGENTS.md §26` — available CLI tools including `agent-sessions`
