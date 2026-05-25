# Runbook: Starting a New Project

This runbook describes the exact steps to start a new project using the master swarm project.

---

## Prerequisites

- This master project is available (cloned or copied)
- You have a clear project idea (even if vague)
- Git is available (optional but recommended)
- bash or PowerShell is available for scripts

---

## Step 1: Copy the Master Project

```bash
# Option A: Clone and strip history
git clone /path/to/master-project /path/to/my-new-project
cd /path/to/my-new-project
rm -rf .git
git init

# Option B: Simple copy
cp -r /path/to/master-project /path/to/my-new-project
cd /path/to/my-new-project
```

**Do not delete:** `.cursor/`, `skills/`, `agents/`, `docs/`, `scripts/`, `templates/`

**Do delete (optional cleanup):**
- `examples/` (keep if you want references)
- `external/upstreams/` (re-clone if needed)
- `state/` (clear any example state)

---

## Step 2: Write README.md

Edit `README.md` to describe your specific project.

**Must include:**
- What the project is (1–2 sentences)
- Why it exists (the problem it solves)
- What success looks like (concrete, specific)
- Any constraints or non-goals

**Example:**
```markdown
# AuthService

A JWT authentication microservice for the Acme Platform.

## Why

The current monolith handles auth poorly — sessions are stateful and don't 
scale horizontally. This service provides stateless JWT auth.

## Success Criteria

- All endpoints return valid JWTs
- JWT validation middleware works in the main platform
- OpenAPI spec is complete and accurate
- Integration tests pass against a real Postgres instance
```

---

## Step 3: Write AGENTS.md

Edit `AGENTS.md` to configure it for your project. The master AGENTS.md contains the full protocol — you only need to add the Project Configuration block at the top:

```yaml
# Project Configuration
project_name: "AuthService"
project_type: "backend-service"
team:
  - orchestrator
  - planner
  - architect
  - coder
  - tester
  - reviewer
  - documenter
  - evaluator
retry_budget:
  per_task: 3
  per_run: 10
confidence_threshold: 0.7
requires_human_approval:
  - deploy
  - publish
  - delete_files
  - external_api_writes
```

For most projects, this is all you need to add. The rest of the AGENTS.md is inherited from the master template.

---

## Step 4: Bootstrap the Project

```bash
bash scripts/bootstrap.sh
```

This will:
1. Verify README.md and AGENTS.md are present
2. Initialize state/ directories
3. Create the first run manifest
4. Validate the AGENTS.md format
5. Emit the first-cycle checklist

If bootstrap fails:
- Missing README.md → write it (Step 2)
- Missing AGENTS.md → add the config block (Step 3)
- Invalid AGENTS.md → check the format against the master template

---

## Step 5: Start the Swarm

```bash
bash scripts/run_swarm_cycle.sh
```

The swarm will:
1. Run project intake (read README + AGENTS, build context)
2. Run repo-recon (if code already exists)
3. Confirm project type
4. Call the planner to decompose goals
5. Route tasks to agents
6. Execute tasks
7. Verify outputs
8. Reflect and update memory

---

## Step 6: Monitor and Intervene

The swarm runs autonomously within its budgets. You may need to intervene when:

**Approval request:** Check `state/runs/<run-id>/approvals-pending.md`
```bash
cat state/runs/*/approvals-pending.md
```

**Blocked task:** Check `state/tasks/<id>/status.md`
```bash
cat state/tasks/*/status.md
```

**Run summary:** When the run completes
```bash
cat state/runs/*/summary.md
```

---

## Step 7: Review Deliverables

When the run completes:
1. Review `state/runs/<run-id>/summary.md` — what was delivered
2. Check `state/artifacts/<release-id>/` — the release package
3. Approve any pending actions in `state/runs/<run-id>/approvals-pending.md`
4. If satisfied: proceed with deployment or publication
5. If not satisfied: add notes to `state/memory/project.md` and start another run

---

## Common Issues and Fixes

| Issue | Fix |
|---|---|
| Bootstrap fails — README too vague | Add specific success criteria |
| Swarm doesn't know project type | Add `project_type:` to AGENTS.md |
| Max iterations reached before completion | Check quality gates, simplify scope, add another run |
| Task blocked — approval needed | Check `approvals-pending.md`, provide approval |
| Wrong agent team selected | Add explicit `team:` to AGENTS.md config block |
| Swarm doing too much | Add scope constraints to README under "Non-Goals" |

---

## Reference

- `templates/README.template.md` — README template
- `templates/AGENTS.template.md` — AGENTS.md template
- `docs/project-types.md` — project type options
- `docs/runbook-recovery.md` — if things go wrong
- `examples/` — complete examples for each project type
