---
id: quality-gate-design
title: Quality Gate Design
version: 1.0
purpose: Define the quality gates appropriate for a project type, establishing concrete pass/fail criteria for each gate.
when_to_use:
  - At the start of a new project to establish quality standards
  - When a new project type needs custom gates
  - When existing gates are insufficient for the project's requirements
when_not_to_use:
  - Mid-project (gates should be defined before work begins)
  - For trivial projects where the universal minimum gates are sufficient
required_inputs:
  - Project type and description
  - Acceptance criteria from task briefs
  - docs/quality-gates.md (existing gates to reuse or extend)
outputs:
  - templates/QUALITY_GATES.template.md (updated if new patterns)
  - state/runs/<run-id>/quality-gates.md (project-specific gate config)
related_docs:
  - docs/quality-gates.md
  - AGENTS.md §9
escalation: If the required quality standards exceed what the current agent team can verify (e.g., legal compliance, security audits), document this gap and request human expert review.
---

# Skill: Quality Gate Design

## Purpose

Produce a quality gate configuration that is concrete, measurable, and appropriate for the project type — not generic, not aspirational.

## Workflow

### Step 1 — Load universal gates

All projects must pass:
1. **Completeness** — all required deliverables are present
2. **Correctness** — outputs meet acceptance criteria
3. **Handoff quality** — operator can proceed without additional agent guidance

### Step 2 — Load project-type gates

From `docs/quality-gates.md`, load gates for the project type:

| Project type | Additional gates |
|---|---|
| Software | test-coverage, no-regressions, api-docs, deployable |
| Research | citations-present, contradictions-addressed, synthesis-complete |
| Data | schema-valid, data-quality-metrics, reproducible-pipeline |
| Docs | internal-links-valid, accuracy-reviewed, sign-off |
| Automation | integration-tested, idempotent, rollback-documented |

### Step 3 — Define gate criteria

For each gate, define:
```yaml
gate_id: test-coverage
name: Test Coverage
description: New code has associated tests
pass_criteria:
  - All new public functions have at least one test
  - All new error paths have a negative test
  - No existing tests are broken
fail_criteria:
  - Any new public function without a test
  - Any failing existing test
evidence_required:
  - Test run output showing pass
  - Coverage report (if available)
retry_budget: 2
```

### Step 4 — Assign gate ownership

Each gate must have an owner agent:
- completeness → evaluator
- correctness → evaluator + tester
- test-coverage → tester
- api-docs → documenter
- citations → researcher
- synthesis → researcher + evaluator

### Step 5 — Write gate configuration

`state/runs/<run-id>/quality-gates.md`:
```markdown
# Quality Gates: <run-id>
Project type: <type>

## Gate: <name>
Status: pending | pass | fail
Owner: <agent>
Pass criteria:
  -
Evidence:
  -
Notes:
```

### Step 6 — Register gates in templates if new

If new gate patterns were designed, update `templates/QUALITY_GATES.template.md` for future reuse.

## Do

- Define gates before work begins, not after
- Make pass criteria specific and measurable
- Assign an owner to every gate

## Don't

- Don't design gates that can't be verified by the available agent team
- Don't design aspirational gates you know will never pass
- Don't leave gates without specific pass criteria
