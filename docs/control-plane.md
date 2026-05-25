# Control Plane

The control plane is the set of files and mechanisms that govern swarm behavior. All authoritative instructions flow through the control plane.

---

## Control Plane Components

### Tier 1: Machine Contracts (Highest Authority)

| File | Purpose | Who reads it | Who writes it |
|---|---|---|---|
| `AGENTS.md` | Full execution contract | All agents | Operator + approved self-improvement |
| `README.md` | Project intent | All agents | Operator |

These files define what is done and how. An agent that ignores them is malfunctioning.

### Tier 2: Behavioral Rules (Durable, Thin)

| Directory | Purpose | Applies to |
|---|---|---|
| `.cursor/rules/*.mdc` | Cursor IDE behavioral rules | All cursor-based agents |

Rules are deliberately thin. They reinforce AGENTS.md protocols without duplicating them.

### Tier 3: Routing Tables (Reference)

| File | Purpose |
|---|---|
| `docs/agent-matrix.md` | Task type → agent → skill routing |
| `docs/project-types.md` | Project type → team + gates |

### Tier 4: Skills and Agent Definitions (Operational)

| Directory | Purpose |
|---|---|
| `skills/*/SKILL.md` | Executable skill interfaces |
| `agents/*.md` | Agent role definitions |

---

## Information Flow

```
Operator writes: README.md + AGENTS.md
                        ↓
Orchestrator reads both → builds context
                        ↓
Planner reads context → builds task graph
                        ↓
Orchestrator reads routing table → dispatches tasks
                        ↓
Agents read skill definitions → execute
                        ↓
Evaluator reads quality gates → validates
                        ↓
Memory curator reads outputs → updates state
```

---

## Control Plane Integrity Rules

1. **AGENTS.md is the final authority** — no rule or skill overrides it
2. **Rules are secondary** — .cursor/rules reinforce, do not override
3. **Skills are interfaces, not policies** — they define how, not whether
4. **Conflicts escalate** — agents do not resolve control plane conflicts unilaterally

---

## Modifying the Control Plane

| Component | Modification Process |
|---|---|
| README.md | Operator edits freely |
| AGENTS.md (project config) | Operator edits configuration block |
| AGENTS.md (protocols) | Requires self-improvement cycle + human approval |
| .cursor/rules/ | Requires self-improvement cycle + human approval |
| skills/*.md | Requires self-improvement cycle + human approval |
| agents/*.md | Requires self-improvement cycle + human approval |
| docs/agent-matrix.md | Requires self-improvement cycle + human approval |

---

## Control Plane Health Checks

Run periodically (or after a failed run):

```bash
# Check for conflicts in AGENTS.md
grep -n "requires_approval\|stop condition\|retry_budget" AGENTS.md

# Check rule files for duplications of AGENTS.md content
grep -r "retry" .cursor/rules/

# Verify skill indexes are current
cat skills/index.md | grep -c "SKILL.md"
```

---

## Related Documents

- `AGENTS.md` — the primary contract
- `.cursor/rules/` — behavioral rules
- `docs/architecture.md` — system architecture
- `docs/self-improvement.md` — how the control plane evolves
