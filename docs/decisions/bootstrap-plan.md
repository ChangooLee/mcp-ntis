# Bootstrap Plan

**Date:** 2026-04-15  
**Status:** Executed  
**Author:** Claude Sonnet 4.6 (autonomous initial build)

---

## Context

This repository started from a blank directory. The mission is to create a reusable "master swarm project" that can bootstrap any future software, research, data, product, documentation, or automation project using only a README.md and AGENTS.md as starting conditions.

---

## Execution Plan

### Phase 1 — Foundation (this session)

1. **Inspect repo** — confirmed blank.
2. **Create this document** — establish the decision log foundation.
3. **Create upstream inventory** — `upstreams/manifest.yaml` mapping all 12 upstream repos.
4. **Create fork/clone/sync scripts** — bash + PowerShell for all platforms.
5. **Create directory skeleton** — full structure per spec.
6. **Populate core contracts** — `README.md`, `AGENTS.md`, `LICENSE`, `.gitignore`.
7. **Create Cursor rules** — 10 thin durable rules in `.cursor/rules/`.
8. **Create skill files** — 17 skills with full `SKILL.md` each.
9. **Create agent files** — 16 agent definitions.
10. **Create docs** — architecture, operating model, runbooks, memory model, etc.
11. **Create templates** — 7 reusable templates.
12. **Create examples** — 4 project type examples with README + AGENTS + gates.
13. **Self-review** — audit for duplication, conflicts, weak spots.
14. **Write reports/self-review.md**.

### Phase 2 — Operator Actions (post-session, requires credentials)

1. Run `scripts/fork_upstreams.sh` after `gh auth login`.
2. Run `scripts/clone_upstreams.sh` to populate `external/upstreams/`.
3. Review `reports/upstream-actions-required.md` for any fork failures.
4. Begin first real project by copying this repo and writing `README.md` + `AGENTS.md`.

---

## Key Design Decisions

### D1: AGENTS.md as machine contract, README.md as operator contract
AGENTS.md is the authoritative instruction set for all agents. README.md is for humans. Neither should duplicate the other in substance.

### D2: Skills are stateless, reusable units; Agents are stateful, role-bearing actors
A skill is invoked; an agent is assigned. Skills are designed to work with multiple agents. Agents are designed to orchestrate skills.

### D3: Upstreams are referenced/adapted, not vendored by default
We document what each upstream contributes conceptually and structurally. Code is only vendored when there is a compelling reason. Scripts handle actual cloning.

### D4: Bounded iteration is non-negotiable
Every swarm loop has explicit retry budgets, max-iteration caps, and stop conditions. Infinite loops are prohibited by rule.

### D5: Memory is layered by scope
Ephemeral task memory → run memory → project memory → reusable pattern memory → operator preference memory. Each layer has explicit retention and eviction policies.

### D6: Project-type routing is declarative
AGENTS.md declares the project type. The orchestrator reads it and selects the agent/skill mix from the routing table in `docs/project-types.md`.

### D7: Quality gates are not optional
All project types have quality gates. Gates vary by project type but always address completeness, correctness, and handoff quality.

### D8: Human approval checkpoints are explicit
AGENTS.md defines which decisions require human approval. The swarm does not self-approve destructive or irreversible actions.

---

## Upstream Integration Rationale

| Upstream | Primary Role |
|---|---|
| agents.md | AGENTS.md contract design |
| anthropics/skills | Skill packaging structure |
| revfactory/harness | Team composition + skill synthesis |
| bytedance/deer-flow | Long-horizon orchestration lifecycle |
| aiming-lab/AutoResearchClaw | Autonomous research loop design |
| supermemoryai/supermemory | Memory model abstraction |
| karpathy/autoresearch | Technical research automation |
| VoltAgent/awesome-claude-code-subagents | Subagent taxonomy and role coverage |
| obra/superpowers | Practical skill methodology |
| dwzhu-pku/PaperBanana | Diagram + report generation hooks |
| msitarzewski/agency-agents | Specialist persona + deliverable orientation |
| HKUDS/ClawTeam | Swarm coordination + convergence design |

---

## Risk Log

| Risk | Mitigation |
|---|---|
| Fork failures (no gh auth) | Scripts continue on failure; retry commands logged |
| Stale upstream content | sync_upstreams.sh maintained; notes/SYNC.md tracks divergence |
| Rule/AGENTS.md duplication | Rules kept thin; AGENTS.md is authoritative for execution contracts |
| Over-engineering | All complexity justified by concrete use cases in examples/ |
