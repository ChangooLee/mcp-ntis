# Decision Framework

This document defines how agents make decisions under uncertainty — when to act unilaterally, when to escalate, and how to reason through tradeoffs.

---

## When to Act vs. When to Escalate

The primary decision an agent must make is whether to proceed independently or escalate. Use this decision tree:

```
Is the action reversible?
├── No (destructive) → Escalate unless already approved
└── Yes → Continue

Is the action within this task's scope?
├── No (scope expansion) → Escalate to orchestrator
└── Yes → Continue

Does this require credentials, external permissions, or budget?
├── Yes → Escalate to operator
└── No → Continue

Does the agent have high confidence in the approach (≥ 0.7)?
├── No → Flag low confidence; consider escalating
└── Yes → Proceed

Do instructions conflict?
├── Yes → Apply AGENTS.md §2 conflict resolution; escalate if unresolvable
└── No → Proceed
```

---

## Decision Categories

### Category 1: Execute Without Escalation

Agents may act unilaterally when:

| Condition | Example |
|---|---|
| Action is reversible and within scope | Creating a new file, editing a draft |
| Task brief explicitly authorizes the action | `requires_approval: false` in brief |
| Action is a standard part of the assigned skill | Researcher runs a search query |
| Confidence ≥ 0.7 | Output quality meets threshold |
| No instruction conflict | Straightforward task execution |

### Category 2: Flag and Continue

Agents should flag the situation and continue executing when:

| Condition | How to Flag |
|---|---|
| Low confidence (0.5–0.7) | Note in task log; mark output as "low confidence" |
| Minor scope expansion discovered | Log to orchestrator; continue current scope |
| Quality gate borderline pass | Note in validation log; mark as "borderline" |
| New information discovered mid-task | Log finding; complete task unless it changes acceptance criteria |

### Category 3: Escalate and Pause

Agents must escalate and wait when:

| Condition | Escalate To |
|---|---|
| Destructive action required (file deletion, data drop) | Operator |
| External communication required (email, API write) | Operator |
| Credentials or permissions needed | Operator |
| Retry budget exhausted | Operator |
| Confidence < 0.5 | Orchestrator, then operator if unresolved |
| Instruction conflict unresolvable | Operator |
| Task scope has expanded significantly | Orchestrator |

### Category 4: Hard Stop

Agents must stop immediately when:

| Condition | Action |
|---|---|
| Credential or secret exposure detected | Hard stop, write stopped.md |
| Security vulnerability found | Hard stop, write red-team report |
| Data deletion not in run scope | Hard stop, write stopped.md |
| AGENTS.md internal contradiction | Hard stop, surface both conflicting clauses |

---

## Confidence Thresholds

| Score | Interpretation | Action |
|---|---|---|
| ≥ 0.9 | High confidence | Proceed; mark output as verified |
| 0.7–0.9 | Good confidence (above threshold) | Proceed normally |
| 0.5–0.7 | Marginal confidence | Proceed with flag; note in log |
| < 0.5 | Low confidence | Escalate; do not present as complete |

**How to estimate confidence:**
- Cross-referenced against 2+ sources → +0.2
- Output matches acceptance criteria exactly → +0.2
- Novel approach not in prior patterns → -0.2
- Source material is sparse or unclear → -0.2
- Adversarial review found no issues → +0.1

Agents are not required to report a numeric score unless the task brief requires it. Qualitative levels (high / medium / low) are sufficient for logs.

---

## Tradeoff Framework

When two valid approaches exist, use this structured reasoning:

### 1. Identify the tradeoffs

| Dimension | Option A | Option B |
|---|---|---|
| Speed | Fast | Slow |
| Confidence | Low | High |
| Reversibility | Irreversible | Reversible |
| Scope alignment | Off-scope | On-scope |
| Risk | High | Low |

### 2. Apply precedence rules

1. **Safety first:** Prefer the option that does not create security risk or data loss
2. **Scope alignment:** Prefer the option that stays within defined scope
3. **Reversibility:** Prefer the option that can be undone
4. **Confidence:** Prefer the option with higher evidence quality
5. **Speed:** Only relevant when all above are equal

### 3. Log the decision

Write to `docs/decisions/<task-id>-<decision>.md`:

```markdown
# Decision: <short title>

Date: <ISO 8601>
Task: <task-id>
Agent: <agent name>

## Options Considered
- Option A: <description>
- Option B: <description>

## Tradeoffs
| Dimension | Option A | Option B |
|---|---|---|
| ... | ... | ... |

## Decision
Option <A|B> chosen because: <reason>

## Risk
<What could go wrong with this choice and how it will be mitigated>
```

---

## Ambiguity Resolution

When task requirements are ambiguous, apply this resolution order:

1. **Check the task brief** — is there a clarifying note?
2. **Check README.md** — does the project intent resolve it?
3. **Check AGENTS.md** — does a protocol cover this?
4. **Check prior decisions** — is there a decision log entry for this pattern?
5. **Check patterns** — `state/memory/patterns/` has recurring solutions
6. **Use the principle of least surprise** — do what the operator most likely intended
7. **If still ambiguous**: escalate to orchestrator with your best interpretation and the alternative

**Never silently pick one interpretation and proceed with a high-stakes action.** Flag ambiguity before acting on irreversible steps.

---

## Scope Boundary Decisions

Agents frequently discover work adjacent to their assigned task. Rules:

| Discovery | Action |
|---|---|
| Small sub-task (<30 min) directly required for current output | Execute it; log to orchestrator |
| Sub-task that would improve quality but not required for acceptance criteria | Skip; log as "improvement opportunity" |
| Sub-task in a different domain (e.g., coder discovers docs gap) | Log it; do not execute (not your role) |
| Sub-task that expands scope significantly | Escalate to orchestrator before executing |
| Critical bug discovered while working on adjacent code | Log it and pause; get orchestrator decision |

---

## Priority Under Time Pressure

When max iterations are approaching (< 2 cycles remaining):

1. Complete in-progress tasks before starting new ones
2. Skip "nice to have" quality improvements
3. Write the best possible output with available time
4. Log what would need to be done in a follow-up run
5. Do not compromise on safety or correctness — only on completeness

When forced to choose between tasks:
- **Critical path first:** tasks that unblock others
- **Irreversible last:** tasks that can't be undone should have most consideration
- **Operator-visible outputs first:** deliverables over internal state updates

---

## Instruction Conflict Resolution

When instructions from different sources conflict:

1. Log both conflicting instructions to `state/runs/<run-id>/conflicts.md`
2. Apply AGENTS.md §2 precedence: AGENTS.md > .cursor/rules > task overrides > agent defaults
3. If the conflict is within AGENTS.md itself: **hard stop**, surface to operator
4. If conflict is between task brief and AGENTS.md §15 (stop conditions): AGENTS.md wins, always
5. If the higher-priority source is ambiguous: apply the more conservative interpretation

**Never resolve a conflict by ignoring one of the instructions silently.** Even when AGENTS.md wins, log that the task-level instruction was overridden.

---

## Decision Quality Criteria

A well-made decision has:

- [x] Considered at least 2 options
- [x] Applied safety precedence
- [x] Stayed within scope
- [x] Logged the reasoning if significant
- [x] Did not escalate unnecessarily (i.e., made the call when it was clearly safe to do so)
- [x] Did not act unilaterally when escalation was required

---

## Related Documents

- `AGENTS.md §2` — instruction precedence
- `AGENTS.md §15` — stop conditions
- `AGENTS.md §17` — escalation conditions
- `AGENTS.md §18` — human approval conditions
- `docs/escalation-model.md` — escalation process
- `docs/quality-gates.md` — confidence and quality thresholds
