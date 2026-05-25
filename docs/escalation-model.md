# Escalation Model

This document specifies the complete escalation paths for the master swarm project — who escalates to whom, under what conditions, and what happens next.

---

## Escalation Levels

```
Level 1: Agent → Orchestrator
Level 2: Orchestrator → Operator (human)
Level 3: Operator → External expert (security, legal, infra team)
```

Escalation always moves up one level at a time. Agents do not skip to the operator without going through the orchestrator first (unless a hard stop condition requires it).

---

## Level 1: Agent → Orchestrator

**Any agent escalates to the orchestrator when:**

| Trigger | Action |
|---|---|
| Routing is ambiguous (no clear primary agent) | Orchestrator re-routes or splits the task |
| A required skill is missing from the agent's skill list | Orchestrator reassigns or adds a supporting agent |
| Task requirements contradict each other | Orchestrator resolves or escalates to operator |
| A dependency task is stuck | Orchestrator unblocks or restructures the task graph |
| An agent completes a task but lacks confidence in the output | Orchestrator triggers evaluator review |
| A sub-task is discovered during execution not in the task graph | Orchestrator adds it to the graph or defers it |

**Format:** Agent writes to `state/runs/<run-id>/escalations.md`:
```markdown
## Escalation from <agent>
Task: <task-id>
Trigger: <specific trigger>
Context: <what was happening>
What I need: <specific resolution needed>
Blocking: <yes | no>
```

---

## Level 2: Orchestrator → Operator

**The orchestrator escalates to the human operator when:**

| Trigger | Action |
|---|---|
| Human approval required (see AGENTS.md §18) | Write to `approvals-pending.md`, pause affected task |
| Retry budget exhausted on a critical task | Write stop reason, request guidance |
| Max run iterations reached | Write `stopped.md`, summarize remaining work |
| Two consecutive cycles blocked for the same reason | Flag systematic blocker |
| Instruction conflict cannot be resolved by precedence rules | Surface both instructions, ask operator to clarify |
| Security-sensitive operation detected | Hard stop, do not proceed |
| Self-improvement change to a core contract is proposed | Request review before applying |
| Confidence threshold not met after all retries | Report low-confidence output; ask whether to use it anyway |

**Format:** `state/runs/<run-id>/approvals-pending.md` or `state/runs/<run-id>/stopped.md`

**Approval timeout:** 72 hours (default). After timeout, the blocked task is marked permanently blocked unless operator responds.

---

## Level 3: Operator → External Expert

**The operator (not the swarm) escalates externally when:**

| Trigger | Who |
|---|---|
| Security vulnerability found by red-team | Security team |
| Legal/compliance concern in research output | Legal team |
| Infrastructure change requires review | DevOps/platform team |
| Dependency on external API requires contract/budget | Procurement/finance |
| Publication requires editorial review | Editorial/comms team |

The swarm does not initiate Level 3 escalations. It flags the need and stops.

---

## Hard Stop Escalations

These bypass Level 1 and go directly to Level 2:

1. **Detected credential exposure** — stop immediately, write to stopped.md, do not continue
2. **Data deletion risk** (not in this run's scope) — hard stop
3. **Security vulnerability found** — hard stop, write red-team report, request operator decision
4. **AGENTS.md internal contradiction** — hard stop, surface both conflicting instructions

---

## Escalation Log Format

Every escalation is recorded in `state/runs/<run-id>/escalations.md`:

```markdown
# Escalation Log: <run-id>

## Escalation E001
Date: <date>
From: <agent>
To: orchestrator | operator
Level: 1 | 2 | 3
Task: <task-id>
Trigger: <specific trigger>
Status: open | resolved | blocked
Resolution: <how resolved, or pending>

---
```

---

## Escalation Resolution SLA

| Level | Expected response |
|---|---|
| Level 1 (agent → orchestrator) | Within the same swarm cycle |
| Level 2 (orchestrator → operator) | 72 hours (configurable via approval_timeout_hours) |
| Level 3 (operator → external) | Depends on external team SLA |

If Level 2 escalation exceeds the timeout:
1. Mark the blocked task `BLOCKED (approval-timeout)`
2. Update run manifest with the blocked status
3. Continue with other non-blocked tasks
4. Write a reminder note to `state/runs/<run-id>/approvals-pending.md`

---

## Escalation vs. Retry

**Retry when:**
- The failure is a task execution error that can be addressed by running again differently
- Retry budget > 0

**Escalate when:**
- The failure is a systemic problem (wrong routing, missing skill, missing info)
- The failure requires a decision the swarm cannot make unilaterally
- Retry budget is exhausted

**Never:**
- Retry without addressing the specific failure reason
- Escalate instead of retrying when the fix is obvious and within budget

---

## Related Documents

- `AGENTS.md §15, §17, §18` — stop conditions, escalation, approval conditions
- `docs/convergence-model.md` — when the run is done vs. stuck
- `docs/runbook-recovery.md` — how to recover from blocked runs
- `docs/runbook-human-approval.md` — approval process detail
