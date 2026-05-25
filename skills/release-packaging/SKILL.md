---
id: release-packaging
title: Release Packaging
version: 1.0
purpose: Package a project deliverable for operator handoff, ensuring completeness, documentation, and reproducibility.
when_to_use:
  - When all quality gates have passed and the project is ready for handoff
  - When preparing a versioned release artifact
  - When creating an operator-ready summary for a completed run
when_not_to_use:
  - Before all quality gates have passed
  - When the project is still in active development
required_inputs:
  - All task outputs in state/tasks/*/outputs/
  - All quality gate reports
  - docs/ (current state)
outputs:
  - state/artifacts/<release-id>/ (packaged deliverable)
  - state/runs/<run-id>/summary.md (final run summary for operator)
  - CHANGELOG.md or equivalent (if applicable)
related_docs:
  - docs/quality-gates.md
  - docs/runbook-new-project.md
  - AGENTS.md §14
escalation: Publishing or deploying any artifact requires human approval. Prepare the package, then pause and request approval before any external action.
---

# Skill: Release Packaging

## Purpose

Produce a deliverable that an operator can take over without asking additional questions.

## Workflow

### Step 1 — Verify quality gates

Confirm all required gates have passed:
- Completeness gate
- Correctness gate
- Documentation gate
- Handoff quality gate

If any gate is not passed: do not proceed. Fix first.

### Step 2 — Collect deliverables

Identify all deliverables for this project type:
- Software: source code, build artifact, migration scripts, deployment config
- Research: synthesis memo, report draft, evidence log, diagram outputs
- Data: schema definitions, pipeline scripts, data quality report
- Docs: published documents, internal links report, review sign-offs

### Step 3 — Write final run summary

`state/runs/<run-id>/summary.md`:
```markdown
# Run Summary: <run-id>
Date: <date>
Project: <name>
Status: complete

## Deliverables
- <deliverable 1>: <location>

## Quality gate status
- Completeness: pass
- Correctness: pass
- Documentation: pass
- Handoff quality: pass

## Known limitations
-

## How to deploy / use
<specific steps for operator>

## Approvals required before publishing
- [ ] <specific action requiring approval>
```

### Step 4 — Create release artifact

Copy deliverables to `state/artifacts/<release-id>/`:
- Maintain directory structure
- Include a manifest listing every file
- Include the run summary

### Step 5 — Prepare changelog entry

If the project uses a changelog:
```markdown
## [<version>] — <date>
### Added
-
### Changed
-
### Fixed
-
```

### Step 6 — Request human approval for publishing

If any external action is needed (deploy, publish, release):
1. Write request to `state/runs/<run-id>/approvals-pending.md`
2. Stop — do not publish without approval

## Do

- Verify gates before packaging
- Write a summary an operator can act on without asking questions
- Request approval before any external action

## Don't

- Don't package before all gates pass
- Don't skip the handoff summary
- Don't deploy or publish autonomously
