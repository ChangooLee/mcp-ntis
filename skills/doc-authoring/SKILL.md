---
id: doc-authoring
title: Documentation Authoring
version: 1.0
purpose: Create or update documentation that is accurate, concise, and sufficient for the intended audience to act on.
when_to_use:
  - After implementing a new feature, API, or system
  - When a quality gate requires documentation freshness
  - When a runbook is missing or outdated
  - For research synthesis outputs
when_not_to_use:
  - For purely internal implementation notes (use task logs instead)
  - For stub documentation before the feature exists
required_inputs:
  - The system/feature being documented (source code, design, or research outputs)
  - Audience definition (who reads this doc)
  - Scope definition (what this doc covers)
outputs:
  - Documentation file in docs/ or inline with code
  - state/tasks/<id>/outputs/doc-checklist.md
related_docs:
  - docs/operating-model.md
  - AGENTS.md §13, §23
escalation: If a document requires information that only the operator has (business context, external system credentials, product decisions), stop and request that information before writing.
---

# Skill: Documentation Authoring

## Purpose

Produce documentation that enables the intended audience to accomplish their goal without additional guidance.

## Workflow

### Step 1 — Define audience and scope

Before writing:
- Who reads this document?
- What do they need to be able to do after reading it?
- What is explicitly out of scope?

### Step 2 — Gather source material

Read the relevant:
- Source code
- Prior documentation (to update, not duplicate)
- Task outputs and logs
- Acceptance criteria

### Step 3 — Choose format

| Audience | Format |
|---|---|
| Operators | Runbook (numbered steps, clear actions) |
| Developers | API reference + integration guide |
| Agents | AGENTS.md style (machine-readable, structured) |
| Researchers | Synthesis memo or report outline |
| End users | User guide (task-oriented, minimal jargon) |

### Step 4 — Write

Structure:
1. **What** — what this is (one sentence)
2. **Why** — why it matters (one sentence)
3. **How** — the main content
4. **Reference** — tables, schemas, examples if needed

Writing rules:
- Active voice
- One idea per paragraph
- Use concrete examples
- Define all acronyms on first use
- Do not write "this document will explain..." — just explain

### Step 5 — Verify accuracy

Cross-check against:
- Source code (does the doc match what the code does?)
- Prior doc (have outdated sections been removed or updated?)
- Task acceptance criteria (is everything required present?)

### Step 6 — Write completion checklist

`state/tasks/<id>/outputs/doc-checklist.md`:
```markdown
# Doc Checklist: <task-id>
Doc file: <path>
Audience: <who>
Accuracy verified: yes | no
Prior doc updated: yes | n/a
Internal links valid: yes | no
Review required: yes | no
```

## Do

- Write for the reader, not for yourself
- Make it possible to act on the doc without asking questions
- Update existing docs rather than creating duplicates

## Don't

- Don't write docs that are already out of date when created
- Don't describe internal implementation details unless specifically for developers maintaining the code
- Don't use excessive headings and bullets that hide the actual content
- Don't pad documents with context that belongs in README.md
