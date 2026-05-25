# Runbook: Software Delivery Project

Step-by-step guide for running a `backend-service`, `frontend-web`, `full-stack`, or `automation-workflow` project through the swarm.

---

## Prerequisites

- README.md written with clear feature requirements
- AGENTS.md configured with `project_type` and team
- `./scripts/bootstrap.sh` has been run

---

## Step 1: Project Intake and Repo Recon

```bash
# Start the swarm cycle — orchestrator runs intake automatically
./scripts/run_swarm_cycle.sh
```

The orchestrator will:
1. Read README.md and AGENTS.md
2. Identify project type and team
3. Run `repo-recon` skill (if existing code is present)
4. Write `state/runs/<run-id>/context.md`
5. Write `state/runs/<run-id>/recon.md`

**Verify:** Check `state/runs/<run-id>/context.md` exists and looks correct before continuing.

---

## Step 2: Decomposition and Planning

The planner will execute `goal-decomposition` and `implementation-planning`:

1. Break the README goals into a task graph
2. Assign each task an agent and skill
3. Identify dependencies and critical path
4. Flag tasks that require human approval

**Output:** `state/tasks/` — one directory per task with `brief.md`

**Human review point:** Review the task graph before execution. If a task is wrong, wrong scope, or wrongly assigned, edit the `brief.md` directly or add a note to `state/runs/<run-id>/context.md`.

---

## Step 3: Architecture Design

For `backend-service`, `full-stack`, and `automation-workflow` projects:

The architect runs `implementation-planning` and defines:
- Interface specifications (HTTP, gRPC, event schemas)
- Module/service boundaries
- Data models
- External dependencies

**Output:** `state/tasks/T00X/outputs/architecture.md` and/or interface specs

**Do not skip this.** Coding before interface design leads to rework.

---

## Step 4: Parallel Execution Phase

The swarm runs multiple tasks in parallel:

| Track | Tasks |
|---|---|
| Code track | coder implements per architecture |
| Test track | tester authors unit + integration tests |
| Docs track | documenter drafts API docs and README |

Run the cycle repeatedly until tasks converge:

```bash
./scripts/run_swarm_cycle.sh  # repeat until all tasks DONE or BLOCKED
```

Check status after each cycle:

```bash
./scripts/health_check.sh
```

---

## Step 5: Quality Gate Check

Run quality gates explicitly:

```bash
./scripts/run_quality_gates.sh
```

For software delivery projects, gates that must pass:
- `sw-test-coverage` — tests cover new code
- `sw-no-regressions` — existing tests still pass
- `sw-api-docs` — public interfaces are documented

**If a gate fails:** The evaluator re-runs the failing task with the gate failure as input. Budget: 2 retries per gate.

---

## Step 6: Adversarial Review (Optional but Recommended)

For security-sensitive features (auth, payments, external APIs):

1. Activate the red-team agent
2. The red-team runs `adversarial-review` against the implementation
3. Severity classification: critical/high/medium/low
4. Critical findings must be resolved before the run can converge

```yaml
# In state/tasks/T_redteam/brief.md
agent: red-team
skill: adversarial-review
target: state/tasks/T00X/outputs/  # the implementation to review
```

---

## Step 7: Debugging Cycle (If Needed)

If tests fail or quality gates don't pass:

1. Debugger runs `bug-triage` — root cause analysis
2. Coder runs `code-implementation` with the triage output as input
3. Tester re-runs test suite

```bash
# Check which tasks are blocked or failed
cat state/runs/<run-id>/manifest.yaml | grep -A3 "status: BLOCKED\|status: FAILED"
```

---

## Step 8: Release Packaging

When all tasks are DONE and all gates pass:

```bash
# The release-manager runs release-packaging
./scripts/run_swarm_cycle.sh
```

The release-manager produces:
- `state/artifacts/release/` — all deliverables
- `state/runs/<run-id>/summary.md` — run summary
- `CHANGELOG.md` or `RELEASE_NOTES.md` (if configured)

---

## Step 9: Human Approval for Deployment

Deployment always requires human approval. Check:

```bash
cat state/runs/<run-id>/approvals-pending.md
```

Approve by editing the file:

```yaml
approved: true
approved_by: <your-name>
approved_at: <ISO 8601>
```

---

## Step 10: Reflection

After the run closes:

```bash
cat state/reflections/<run-id>.md
```

The reflection contains:
- What worked well
- What failed and root causes
- Proposed improvements (skills, agents, quality gates)
- Pattern discoveries

Review and approve any self-improvement proposals (see `docs/self-improvement.md`).

---

## Common Problems

### Tests Fail After Code Change

1. Run `./scripts/health_check.sh` to identify which task failed
2. Read `state/tasks/<id>/log.md` for the failure reason
3. Check if tester and coder are working from the same interface spec
4. Assign a debugger task if the cause is unclear

### Task Is Stuck (BLOCKED for 2+ Cycles)

See `docs/runbook-recovery.md §3 — Systematic Blocker`.

### Approval Not Coming

Check `state/runs/<run-id>/approvals-pending.md` — the 72h timeout will expire and mark tasks permanently blocked. Provide approval or reject explicitly.

### Architecture Changes Mid-Run

1. Update the interface spec
2. Mark affected tasks as PENDING (reset them)
3. Add a context note to `state/runs/<run-id>/context.md`
4. Continue the cycle — planner will re-route

---

## Related Documents

- `docs/task-lifecycle.md` — task state machine
- `docs/quality-gates.md` — gate definitions
- `docs/runbook-recovery.md` — recovery procedures
- `docs/runbook-human-approval.md` — approval process
- `docs/escalation-model.md` — escalation paths
