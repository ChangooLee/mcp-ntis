---
id: project-bootstrap
title: Project Bootstrap
version: 1.0
purpose: Initialize a new project using this master project as the base, creating all required starting files and state from templates.
when_to_use:
  - When starting a brand new project
  - When copying the master project into a new directory
  - When a project needs to be re-initialized from scratch
when_not_to_use:
  - On an existing project with substantial content (would overwrite it)
  - Mid-run on a project already in progress
required_inputs:
  - Project name
  - Project type
  - README.md first draft (or at least a description to draft from)
outputs:
  - Initialized README.md (from template if blank)
  - Initialized AGENTS.md (from template, configured for project type)
  - state/ directory structure
  - First run manifest
related_docs:
  - docs/runbook-new-project.md
  - templates/README.template.md
  - templates/AGENTS.template.md
escalation: If the project type is ambiguous after intake, do not guess — ask the operator before bootstrapping.
---

# Skill: Project Bootstrap

## Purpose

Get a new project from zero to first-run-ready in the shortest path: correct templates, correct state, correct agent configuration.

## Workflow

### Step 1 — Confirm prerequisites

1. Does `README.md` exist? If not: draft from `templates/README.template.md`
2. Does `AGENTS.md` exist? If not: copy from `templates/AGENTS.template.md`
3. What is the project type? (required before bootstrap)

### Step 2 — Initialize AGENTS.md

If AGENTS.md is the master template, configure it for this project:
```yaml
project_name: "<name>"
project_type: "<type>"
team:
  - orchestrator
  - planner
  # project-type-appropriate team
```

Remove sections not relevant to this project type to reduce noise.

### Step 3 — Initialize state directories

```bash
mkdir -p state/tasks state/runs state/reflections state/memory state/artifacts
echo "# Project Memory\nProject: <name>\nStatus: initialized" > state/memory/project.md
```

### Step 4 — Create first run manifest

`state/runs/<YYYYMMDD-HHmmss>/manifest.yaml`:
```yaml
run_id: <YYYYMMDD-HHmmss>
project_name: <name>
project_type: <type>
status: bootstrapped
started_at: <timestamp>
max_iterations: 10
current_iteration: 0
tasks_total: 0
tasks_done: 0
tasks_blocked: 0
```

### Step 5 — Copy relevant templates

For the project type, copy relevant templates to the project:
- `templates/PROJECT_BRIEF.template.md` → `docs/project-brief.md`
- `templates/QUALITY_GATES.template.md` → `docs/quality-gates.md`
- `templates/TASK.template.md` → stays in `state/tasks/` for use during decomposition

### Step 6 — Confirm bootstrap

Write `state/runs/<run-id>/bootstrap-complete.md`:
```markdown
# Bootstrap Complete
Date: <date>
Project: <name>
Type: <type>
Files initialized:
  - README.md
  - AGENTS.md
  - state/memory/project.md
  - state/runs/<run-id>/manifest.yaml
Next step: run `bash scripts/run_swarm_cycle.sh`
```

## Do

- Verify README.md and AGENTS.md exist before starting the swarm
- Configure AGENTS.md for the specific project type
- Initialize state directories before the first run

## Don't

- Don't overwrite existing content in README.md or AGENTS.md without confirmation
- Don't bootstrap without a project type — ask first
- Don't skip state initialization — missing directories cause confusing failures
