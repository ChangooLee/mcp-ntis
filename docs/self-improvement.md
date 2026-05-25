# Self-Improvement

This document describes how the master swarm project improves itself over time through controlled, evidence-based changes.

---

## Philosophy

Self-improvement is not automatic rewriting. It is:
1. A systematic failure → reflection → proposal → approval → application cycle
2. Bounded: only triggered by evidence, not by speculation
3. Controlled: core contracts (AGENTS.md, rules, skills, agent defs) require human approval
4. Traceable: every change has a documented reason and evidence source

---

## The Self-Improvement Cycle

```
Run completes or stops
  ↓
Retrospective (skills/retrospective-and-reflection)
  ↓
Patterns identified
  ↓
Improvement proposals generated
  ↓
Is it a core contract? → Yes → Human review required
                       → No  → Apply autonomously
  ↓
Apply change
  ↓
Test on next run
  ↓
If improved: keep; if worse: revert
```

---

## What Can Be Improved Autonomously

Changes that don't touch core contracts can be applied without human approval:
- `state/memory/patterns/` — new pattern entries
- `templates/` — template updates based on patterns
- `examples/` — example improvements
- `docs/` — documentation updates (not operational model docs)
- `state/reflections/` — failure analysis entries

---

## What Requires Human Approval

Core contracts that affect all future swarm behavior:
- `AGENTS.md` — the machine contract
- `.cursor/rules/*.mdc` — behavioral rules
- `skills/*/SKILL.md` — skill interfaces and workflows
- `agents/*.md` — agent definitions and escalation chains
- `docs/operating-model.md` — the swarm loop definition
- `docs/quality-gates.md` — gate criteria

**Why:** These files define how all future runs behave. A bad change to AGENTS.md could corrupt all future runs.

---

## Improvement Proposal Format

Log proposals in `docs/decisions/<YYYY-MM-DD>-improvement-<slug>.md`:

```markdown
# Improvement Proposal: <title>
Date: <date>
Proposed by: <agent>
Evidence: <state/reflections/<run-id>.md, section X>
Status: proposed | approved | rejected | applied

## Problem
<Specific failure or inefficiency observed>

## Root Cause
<Why it happens>

## Proposed Change
File: <file to change>
Change: <what to change>
Expected outcome: <how this fixes the problem>

## Risk
<What could go wrong if this change is wrong>

## Success Metric
<How we'll know if it worked on the next run>
```

---

## Improvement Commit Format

When applying an approved improvement:

```
[self-improve] <scope>: <description>

Reason: <specific failure or pattern>
Evidence: <run-id or reflection reference>
Approved-by: <name or "autonomous">
Proposal: docs/decisions/<date>-improvement-<slug>.md
```

---

## Improvement Taxonomy

| Category | Examples | Approval Required |
|---|---|---|
| Pattern memory | New pattern for data-etl projects | No |
| Template update | Better task brief format | No |
| Skill workflow | Fix step ordering in bug-triage | Yes |
| Agent scope | Clarify reviewer vs. evaluator boundary | Yes |
| Quality gate | Add new gate for security projects | Yes |
| AGENTS.md protocol | Tighter retry budget | Yes |
| Cursor rule | New routing rule | Yes |

---

## Improvement Anti-Patterns

Do NOT:
- Apply improvements without evidence ("I think this would be better")
- Make improvements that are too broad ("rewrite the whole skill")
- Make multiple unrelated improvements in one change
- Apply core contract changes without human approval
- Revert improvements silently (revert with documented reason)

---

## Tracking Improvements Over Time

A log of applied improvements lives in `docs/decisions/`. Each entry:
- Starts as `proposed`
- Moves to `approved` or `rejected`
- Moves to `applied` when the change is made
- Gets a follow-up note after the next run

**Quarterly review:** Check the improvement log. Are improvements actually working? Revert any that aren't.

---

## Related Documents

- `skills/retrospective-and-reflection/SKILL.md` — how improvements are identified
- `.cursor/rules/50-reflection-and-self-improvement.mdc` — rules for improvement cycle
- `AGENTS.md §10, §11` — reflection and self-improvement protocols
- `docs/decisions/` — improvement proposal archive
