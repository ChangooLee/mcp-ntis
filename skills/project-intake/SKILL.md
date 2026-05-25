---
id: project-intake
title: Project Intake
version: 1.0
purpose: Gather, validate, and structure all information needed to begin a swarm run on a new or resumed project.
when_to_use:
  - Starting a new project run (no prior state exists)
  - Resuming a project after a gap (prior state exists but context is stale)
  - When project scope has significantly changed and re-intake is needed
when_not_to_use:
  - Mid-run task execution (use the task brief directly)
  - When intake has already been completed this run (check state/runs/<id>/context.md)
required_inputs:
  - README.md (project description)
  - AGENTS.md (machine contract)
outputs:
  - state/runs/<run-id>/context.md (structured context)
  - state/runs/<run-id>/manifest.yaml (run manifest)
  - .cursor/plans/<run-id>-intake.md (initial plan)
related_docs:
  - docs/operating-model.md
  - docs/project-types.md
  - AGENTS.md §3
escalation: If README.md is absent or uninterpretable, stop and request operator input before proceeding.
---

# Skill: Project Intake

## Purpose

Produce a structured context document that tells the swarm exactly what project it is working on, what type it is, what success looks like, and what the first actions should be.

## Workflow

### Step 1 — Read primary contracts

1. Read `README.md` in full
2. Read `AGENTS.md` in full
3. Note any contradictions between them (AGENTS.md wins for execution, README for intent)

### Step 2 — Extract structured information

Extract and record:
- Project name and one-sentence description
- Project type (explicit or inferred)
- Success criteria (explicit or inferred from README)
- Key stakeholders or operator name (if present)
- Technology stack and constraints (if mentioned)
- Known dependencies or external services
- Explicit team composition (if specified in AGENTS.md)
- Retry budgets and confidence thresholds (from AGENTS.md or defaults)

### Step 3 — Check prior state

1. List `state/runs/` — is there a prior run?
2. If yes: read `state/runs/<latest>/manifest.yaml` and `state/memory/project.md`
3. Identify what was completed, what is in progress, and what is blocked
4. Determine: fresh start or resume?

### Step 4 — Create run manifest

Create `state/runs/<YYYYMMDD-HHmmss>/manifest.yaml`:
```yaml
run_id: <YYYYMMDD-HHmmss>
project_name: ""
project_type: ""
status: started
started_at: ""
max_iterations: 10
current_iteration: 0
tasks_total: 0
tasks_done: 0
tasks_blocked: 0
```

### Step 5 — Write context document

Write `state/runs/<run-id>/context.md`:
```markdown
# Run Context: <run-id>
Project: <name>
Type: <type>
Status: fresh | resumed
Success criteria:
  - 
Prior context summary:
  -
First actions:
  1.
```

### Step 6 — Confirm project type

Confirm or infer `project_type`. If ambiguous after reading both files:
- List 2–3 candidate types with reasoning
- Select the most likely one
- Flag the ambiguity in the context document for operator review

## Examples

**Good intake output:**
```
Project: AuthService — JWT authentication microservice
Type: backend-service
Success criteria: All endpoints tested, OpenAPI spec complete, deployed to staging
Prior context: None (fresh start)
First actions:
  1. Run repo-recon skill
  2. Decompose into task graph
  3. Route to architect + coder
```

**Bad intake:**
```
Project looks like some kind of backend thing. Let's start coding.
```

## Do

- Extract specific success criteria, not just "do a good job"
- Infer project type if not explicit — don't stall
- Record the intake in state so it can be resumed

## Don't

- Don't proceed if README.md is absent — escalate
- Don't skip prior state check — resuming is cheaper than restarting
- Don't guess project type on ambiguous signals — flag it
