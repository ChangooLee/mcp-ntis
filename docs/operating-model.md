# Operating Model

This document defines how the master swarm project operates: the loop, the agents, the constraints, and the convergence criteria.

---

## The Swarm Loop

The swarm executes a bounded iteration loop. Every run follows this sequence:

```
┌─────────────────────────────────────────────────────────────┐
│                      SWARM LOOP                             │
│                                                             │
│  1. INTAKE          Read README + AGENTS. Build context.    │
│  2. RECON           Map existing repo state.                │
│  3. TYPE            Identify/confirm project type.          │
│  4. DECOMPOSE       Break goals into task graph.            │
│  5. PLAN            Create plans for complex tasks.         │
│  6. ROUTE           Assign tasks to agents.                 │
│  7. EXECUTE         Dispatch and run tasks.                 │
│  8. VERIFY          Run quality gates.                      │
│  9. REFLECT         Retrospective + memory update.          │
│ 10. RETRY/COMPLETE  Bounded retry or exit.                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Roles in the Loop

| Phase | Primary Agent | Supporting |
|---|---|---|
| Intake | orchestrator | project-bootstrapper |
| Recon | orchestrator | architect |
| Type | orchestrator | product-manager |
| Decompose | planner | orchestrator |
| Plan | planner | architect |
| Route | orchestrator | — |
| Execute | coder / researcher / documenter / tester | reviewer, debugger |
| Verify | evaluator | tester, red-team (if activated) |
| Reflect | orchestrator | memory-curator |
| Retry | orchestrator | (original agent) |

---

## Bounded Iteration

Every run is bounded. There are no infinite loops.

| Bound | Default | Override |
|---|---|---|
| Per-task retries | 3 | `task.retry_budget` in task brief |
| Max run iterations | 10 | `run.max_iterations` in AGENTS.md |
| Quality gate retries | 2 | `gates.retry_budget` in AGENTS.md |
| Research iterations | 5 | `research.max_iterations` in AGENTS.md |

When any budget is exhausted: escalate, do not continue.

---

## Stop Conditions

The loop stops when:

1. All tasks are DONE (successful completion)
2. Max iterations reached (incomplete — human review needed)
3. Stop condition triggered from AGENTS.md §15
4. Catastrophic failure (security event, data loss risk, unresolvable conflict)

On stop: write `state/runs/<run-id>/stopped.md` with reason. Do not discard partial work.

---

## Convergence Criteria

The run converges (successfully) when:

- All leaf tasks in the task graph are DONE
- All project-level quality gates pass
- Final run summary is written
- Memory is updated

---

## Agent Coordination Protocol

1. **One orchestrator per run** — it owns the loop and all routing decisions
2. **Agents are dispatched, not autonomous** — they don't self-assign tasks
3. **Handoffs are explicit** — every agent writes its output before handing off
4. **Conflicts escalate** — agents do not resolve conflicts between themselves unilaterally
5. **Human approval halts the loop** — the loop pauses, not fails, while waiting for approval

---

## Integration with Upstreams

This operating model is shaped by:

- **DeerFlow (bytedance):** Multi-step task lifecycle, coordinator/subagent model
- **ClawTeam (HKUDS):** Team-based execution, convergence design
- **AutoResearchClaw:** Research loop within the broader execution loop
- **harness (revfactory):** Agent team composition by domain/project type

---

## Related Documents

- `docs/task-lifecycle.md` — per-task lifecycle detail
- `docs/agent-matrix.md` — agent routing table
- `docs/quality-gates.md` — gate definitions
- `docs/memory-model.md` — state and memory model
- `AGENTS.md` — machine contract (authoritative)
