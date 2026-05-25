---
id: retrospective-and-reflection
title: Retrospective and Reflection
version: 1.0
purpose: Produce a structured retrospective after a run that identifies successes, failures, root causes, and concrete improvements.
when_to_use:
  - After every completed run
  - After every stopped run (early stop is when reflection is most needed)
  - After a systematic failure is identified mid-run
when_not_to_use:
  - Mid-task (wait until task or run boundary)
  - As a substitute for actual debugging (use bug-triage first)
required_inputs:
  - state/runs/<run-id>/manifest.yaml
  - state/tasks/<id>/log.md (for each task in the run)
  - state/tasks/<id>/validation.md (for each task)
outputs:
  - state/reflections/<run-id>.md (structured retrospective)
  - Proposed improvements (to skills, agents, gates, AGENTS.md)
related_docs:
  - docs/self-improvement.md
  - AGENTS.md §10, §11
escalation: If the retrospective identifies a systematic failure that requires changes to AGENTS.md or core rules, do not apply them autonomously — propose them and escalate for human review.
---

# Skill: Retrospective and Reflection

## Purpose

Produce a retrospective that is specific enough to drive concrete improvements, not generic enough to be useless.

## Workflow

### Step 1 — Gather run data

Read:
- All task logs from this run
- All validation reports
- Run manifest (completion status, iteration count)
- Any escalation or approval requests

### Step 2 — Assess what succeeded

For each task that completed successfully:
- What approach worked?
- Was the plan followed or was improvisation needed?
- Were there any surprising findings?

### Step 3 — Analyze failures

For each task that failed or was blocked:
- What was the expected outcome?
- What actually happened?
- Root cause category (logic error, missing info, wrong routing, scope issue, external block)
- Contributing factors
- Could this have been predicted at planning time?

### Step 4 — Identify patterns

Look for patterns across multiple tasks:
- The same type of failure in multiple tasks
- The same agent struggling with the same issue
- Quality gates that consistently fail

### Step 5 — Generate improvement proposals

For each significant failure pattern:
1. Name the pattern
2. Propose a specific change: skill update, agent change, new rule, quality gate
3. Estimate the impact if applied
4. Note whether it requires human approval (core contract change) or can be applied autonomously

### Step 6 — Write retrospective

`state/reflections/<run-id>.md`:
```markdown
# Retrospective: <run-id>
Date: <date>
Run status: completed | stopped | blocked
Iterations used: <n> / <max>
Tasks completed: <n>
Tasks blocked: <n>

## What succeeded
-

## What failed
### <failure 1>
Root cause:
Contributing factors:
Could have been prevented by:

## Patterns identified
-

## Improvement proposals
### <proposal 1>
Type: skill | agent | rule | gate | AGENTS.md
Specific change:
Requires human approval: yes | no
Evidence: <task-id or log reference>

## Next run recommendations
1.
2.
```

## Do

- Be specific about root causes — "it didn't work" is not a root cause
- Propose specific changes, not vague improvements
- Distinguish between one-off failures and systematic patterns

## Don't

- Don't write a reflection that is just a summary of what happened
- Don't propose improvements without evidence
- Don't propose changes to core contracts without flagging them for human review
- Don't skip reflection when a run fails — that is when it matters most
