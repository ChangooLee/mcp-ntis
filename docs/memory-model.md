# Memory Model

This document specifies the layered memory model used by the master swarm project.

Conceptually shaped by: Supermemory (supermemoryai/supermemory) — specifically its layered persistence and retrieval priority patterns. No Supermemory product code is used.

---

## Memory Layers

The memory model has 5 layers, from most ephemeral to most persistent.

```
┌────────────────────────────────────────────────────┐
│  Layer 5: Operator Preference Memory               │ ← Most persistent
│  state/memory/operator-prefs.md                    │
├────────────────────────────────────────────────────┤
│  Layer 4: Reusable Pattern Memory                  │
│  state/memory/patterns/                            │
├────────────────────────────────────────────────────┤
│  Layer 3: Project Memory                           │
│  state/memory/project.md                           │
├────────────────────────────────────────────────────┤
│  Layer 2: Run Memory                               │
│  state/runs/<run-id>/                              │
├────────────────────────────────────────────────────┤
│  Layer 1: Task Memory                              │ ← Most ephemeral
│  state/tasks/<id>/                                 │
└────────────────────────────────────────────────────┘
```

---

## Layer 1: Task Memory (Ephemeral)

**Scope:** Single task execution  
**Location:** `state/tasks/<id>/`  
**Retention:** 30 days after DONE status  
**Contents:**
- Task brief
- Execution log
- Outputs
- Validation results
- Review or triage reports

**What gets discarded:** All per-task scratch state after the task is complete.  
**What gets promoted:** Significant findings are summarized into run memory or pattern memory.

---

## Layer 2: Run Memory

**Scope:** Single swarm run  
**Location:** `state/runs/<run-id>/`  
**Retention:** 90 days  
**Contents:**
- Run manifest (status, iterations, task counts)
- Context document (intake output)
- Task graph and routing decisions
- Cycle logs
- Escalation log
- Approvals pending
- Final summary

**What gets discarded:** Routine cycle-level details after run completes.  
**What gets promoted:** Key findings to project memory; patterns to pattern memory; decisions to docs/decisions/.

---

## Layer 3: Project Memory

**Scope:** Entire project lifecycle  
**Location:** `state/memory/project.md`  
**Retention:** Permanent (deleted only when project is archived)  
**Contents:**
- Current project status
- Completed milestones
- In-progress work
- Known blockers
- Key architectural decisions (summary — full detail in docs/decisions/)
- Patterns discovered
- Failure history (summary — full detail in state/reflections/)

**Update cadence:** After every task that changes shared state. After every run.

**Conflict resolution:** If project.md contradicts current repo state, trust the repo. Update project.md.

---

## Layer 4: Reusable Pattern Memory

**Scope:** Cross-project, cross-run  
**Location:** `state/memory/patterns/<topic>.md`  
**Retention:** Permanent (review annually for relevance)  
**Contents:**
- Pattern name and description
- When it applies (project types, contexts)
- How to apply it
- Evidence (run IDs where it worked)
- Anti-pattern (what not to do)

**Update cadence:** When retrospective identifies a reusable pattern.

**Examples of patterns:**
- "For data-etl projects with > 1M rows, add a dry-run flag before full execution"
- "Research questions that can't be bounded in 5 iterations need scope reduction"
- "Integration tests that require containers should be in a separate suite"

---

## Layer 5: Operator Preference Memory

**Scope:** Operator-specific preferences across all projects  
**Location:** `state/memory/operator-prefs.md`  
**Retention:** Permanent  
**Contents:**
- Preferred technology choices
- Communication style preferences
- Risk tolerance
- Common approval patterns

**Update cadence:** When operator gives explicit direction or corrects swarm behavior.

---

## Retrieval Priority

When loading context for a new task, load in this priority order:

1. `state/memory/project.md` — current project state (highest priority)
2. `state/runs/<latest-run-id>/context.md` — most recent run context
3. `state/memory/patterns/` — relevant patterns for current task type
4. `state/reflections/` — recent failures relevant to current task type
5. `state/memory/operator-prefs.md` — operator preferences

**When memory conflicts with repo state:** Always trust current repo state. Memory is a cache; the repo is the source of truth.

---

## What Is NOT Stored in Memory

- Credentials, API keys, or passwords
- PII or personally identifiable information
- Raw LLM outputs without curation
- Stale context from > 30-day-old completed tasks
- Temporary file paths or machine-specific paths

---

## Stale Memory Handling

Memory becomes stale when:
- Project status changes but project.md is not updated
- A pattern is discovered to be incorrect
- An operator preference is reversed

When stale memory is detected:
1. Note the conflict (memory vs. reality)
2. Trust reality
3. Update or remove the stale memory entry
4. Log the correction in state/reflections/ if material

---

## Decision Memory

Decisions live in `docs/decisions/` (not in state/memory/) because they are durable documentation, not runtime state. The memory model references decisions by linking to decision log entries.

---

## Related Documents

- `state/memory/README.md` — memory directory guide
- `skills/memory-update/SKILL.md` — how to update memory
- `AGENTS.md §12` — memory update protocol
- `docs/self-improvement.md` — how patterns feed into self-improvement
