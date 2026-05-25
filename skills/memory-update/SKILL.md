---
id: memory-update
title: Memory Update
version: 1.0
purpose: Update the project's persistent memory after a task or run completes, ensuring future runs have accurate context.
when_to_use:
  - After any task that changes shared project state
  - After every completed or stopped run
  - When a new pattern or decision is identified
when_not_to_use:
  - Mid-task (update after completion, not during)
  - For ephemeral task-level state (use task logs)
required_inputs:
  - state/tasks/<id>/log.md (what changed)
  - state/runs/<run-id>/manifest.yaml (run status)
  - state/reflections/<run-id>.md (if reflection is complete)
outputs:
  - state/memory/project.md (updated)
  - state/memory/patterns/<topic>.md (if new pattern)
  - docs/decisions/<date>-<slug>.md (if new decision)
related_docs:
  - docs/memory-model.md
  - AGENTS.md §12
escalation: If a memory conflict is detected (memory says X, repo says Y), always trust the repo and update memory to reflect reality.
---

# Skill: Memory Update

## Purpose

Keep the project memory accurate and useful for future runs. Bad memory is worse than no memory.

## Workflow

### Step 1 — Identify what changed

Review:
- Task logs from this run
- Run manifest
- Any decisions made
- Any patterns discovered
- Any failures encountered

### Step 2 — Update project memory

Read `state/memory/project.md` (create if absent):
```markdown
# Project Memory
Last updated: <date>
Project name: <name>
Project type: <type>
Current status: <in-progress | paused | blocked | complete>
Completed milestones:
  -
Current in-progress:
  -
Known blockers:
  -
Key decisions:
  -
Architecture notes:
  -
Patterns discovered:
  -
```

Update only the relevant sections. Do not erase history — append new entries.

### Step 3 — Update pattern memory (if new pattern)

If a reusable pattern was discovered:
Create `state/memory/patterns/<topic>.md`:
```markdown
# Pattern: <name>
Date discovered: <date>
Project type: <types this applies to>
Context: <when this pattern applies>
Pattern:
  <what to do>
Evidence:
  - <run-id where this worked>
Anti-pattern:
  <what to avoid>
```

### Step 4 — Log decisions

If a significant decision was made:
Create `docs/decisions/<YYYY-MM-DD>-<slug>.md`:
```markdown
# Decision: <title>
Date: <date>
Status: accepted
Context: <why this decision was needed>
Decision: <what was decided>
Consequences: <what this means going forward>
Alternatives considered:
  -
```

### Step 5 — Update run manifest

Update `state/runs/<run-id>/manifest.yaml`:
```yaml
status: completed | stopped | blocked
completed_at: <timestamp>
tasks_done: <count>
tasks_blocked: <count>
memory_updated: true
```

### Step 6 — Prune stale state

Check for task state older than 30 days with status DONE:
- Archive or delete `state/tasks/<old-id>/` to keep state manageable
- Do not prune reflections or patterns

## Do

- Update memory after every run, even if it failed
- Record failures — they are the most valuable memory
- Verify memory against current repo state before writing

## Don't

- Don't overwrite prior history — append
- Don't write sensitive data (passwords, tokens) to memory files
- Don't update memory mid-task — wait until the task is complete or stopped
