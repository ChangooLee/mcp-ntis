# Upstream Integration Documentation

This document records every upstream repository integrated into the master swarm project: what it is, how it is used, and what we did not take from it.

Machine-readable inventory: `upstreams/manifest.yaml`

---

## agents.md — `agentsmd/agents.md`

**URL:** https://github.com/agentsmd/agents.md  
**Local path:** `external/upstreams/agents.md`  
**Integration mode:** Referenced  
**License:** MIT

**What we use:**  
The conceptual contract for what AGENTS.md should be: a machine-readable, authoritative instruction file that governs agent behavior within a repository. Specifically: the principle that AGENTS.md is the single source of truth for agent execution behavior, and that it should have predictable sections.

**What we adapted:**  
We extended the concept significantly with: intake protocol, decomposition protocol, routing, validation, reflection, self-improvement, memory update, stop conditions, retry budgets, escalation conditions, and safe-edit rules. Our AGENTS.md is a superset.

**What we excluded:**  
Platform-specific tool integrations from the upstream.

**Sync strategy:** Monthly check for upstream updates. Review if new sections appear in the upstream template.

---

## skills — `anthropics/skills`

**URL:** https://github.com/anthropics/skills  
**Local path:** `external/upstreams/skills`  
**Integration mode:** Adapted  
**License:** MIT / Apache-2.0

**What we use:**  
The canonical packaging structure for Claude Code skills: one folder per skill, SKILL.md as the interface file, YAML frontmatter, and the principle that skills are reusable and explicitly invoked (not implicit behaviors).

**What we adapted:**  
Extended the SKILL.md frontmatter with: `when_not_to_use`, `related_docs`, `escalation`. Added a skills index (skills/index.md). Added 17 project-specific skills.

**What we excluded:**  
Platform-specific Anthropic internal integrations.

**Sync strategy:** Monthly. If new skill format conventions appear upstream, evaluate and adopt.

---

## harness — `revfactory/harness`

**URL:** https://github.com/revfactory/harness  
**Local path:** `external/upstreams/harness`  
**Integration mode:** Referenced  
**License:** Check upstream

**What we use:**  
Domain team generation patterns and the idea of synthesizing an agent team based on project type. The concept of agent-to-skill affinity mapping.

**What we adapted:**  
Our agent-matrix.md and the project-type routing in .cursor/rules/90-project-type-routing.mdc draw on these patterns.

**What we excluded:**  
Any runtime harness code specific to the upstream's execution environment.

**Sync strategy:** Quarterly. Check for new team composition patterns.

---

## deer-flow — `bytedance/deer-flow`

**URL:** https://github.com/bytedance/deer-flow  
**Local path:** `external/upstreams/deer-flow`  
**Integration mode:** Referenced  
**License:** Apache-2.0

**What we use:**  
Long-horizon orchestration: multi-step task lifecycle, the coordinator/subagent delegation model, memory abstractions for multi-turn tasks, and the concept of minutes-to-hours task handling.

**What we adapted:**  
The swarm loop in docs/operating-model.md and scripts/run_swarm_cycle.sh operationalize these patterns. The memory model layers are shaped by the DeerFlow memory abstraction.

**What we excluded:**  
Python-specific runtime code, specific LLM client integrations.

**Sync strategy:** Quarterly.

---

## AutoResearchClaw — `aiming-lab/AutoResearchClaw`

**URL:** https://github.com/aiming-lab/AutoResearchClaw  
**Local path:** `external/upstreams/AutoResearchClaw`  
**Integration mode:** Referenced  
**License:** Check upstream

**What we use:**  
The autonomous research loop design: self-evolving iteration, the hypothesis → investigation → evidence → output cycle, and the principle of automated self-refinement based on contradiction detection.

**What we adapted:**  
Our research mode (docs/research-mode.md), the factual-research skill, and the researcher agent all draw on these patterns. The research sub-loop within the swarm loop is directly inspired by this upstream.

**What we excluded:**  
Specific ML model integrations, academic crawler code requiring external API keys.

**Sync strategy:** Quarterly.

---

## supermemory — `supermemoryai/supermemory`

**URL:** https://github.com/supermemoryai/supermemory  
**Local path:** `external/upstreams/supermemory`  
**Integration mode:** Referenced (concepts only)  
**License:** Apache-2.0

**What we use:**  
The concept of layered memory (ephemeral → persistent → organizational), retrieval priority ordering, and separation of memory types by scope and lifetime.

**What we adapted:**  
Our docs/memory-model.md is directly shaped by these concepts. The 5-layer model (task → run → project → pattern → operator prefs) reflects the Supermemory layered approach.

**What we excluded:**  
All product code, APIs, cloud service integrations. We implement the conceptual model ourselves using flat markdown files.

**Sync strategy:** Quarterly. Check if new memory abstraction patterns emerge.

---

## autoresearch — `karpathy/autoresearch`

**URL:** https://github.com/karpathy/autoresearch  
**Local path:** `external/upstreams/autoresearch`  
**Integration mode:** Referenced  
**License:** MIT

**What we use:**  
Iterative evidence-gathering patterns, the structured experiment summary format, and the concept of an autonomous research loop with a convergence criterion.

**What we adapted:**  
Influences the researcher agent protocol and the research cycle templates. The evidence log format is shaped by this upstream's experiment summary format.

**What we excluded:**  
Python-specific tooling, Jupyter notebook workflows.

**Sync strategy:** Quarterly.

---

## awesome-claude-code-subagents — `VoltAgent/awesome-claude-code-subagents`

**URL:** https://github.com/VoltAgent/awesome-claude-code-subagents  
**Local path:** `external/upstreams/awesome-claude-code-subagents`  
**Integration mode:** Referenced  
**License:** Check upstream

**What we use:**  
A taxonomy of Claude Code subagent roles, used to inform our agent catalog coverage and ensure we have specialist role coverage for all common task types.

**What we adapted:**  
Our agents/ catalog covers the key roles identified in this taxonomy. We added or adapted roles for our specific needs (memory-curator, project-bootstrapper, prompt-engineer).

**What we excluded:**  
Individual subagent implementations that are too platform-specific.

**Sync strategy:** Quarterly. Check if new role categories emerge.

---

## superpowers — `obra/superpowers`

**URL:** https://github.com/obra/superpowers  
**Local path:** `external/upstreams/superpowers`  
**Integration mode:** Adapted  
**License:** Check upstream

**What we use:**  
The principle that skills are concrete executable procedures with defined interfaces, not vague descriptions. Practical software development workflow patterns.

**What we adapted:**  
Our SKILL.md format and the principle of skill-level documentation draw on this upstream. Several software development skills reflect workflow patterns from this upstream.

**What we excluded:**  
Platform-specific integrations.

**Sync strategy:** Quarterly.

---

## PaperBanana — `dwzhu-pku/PaperBanana`

**URL:** https://github.com/dwzhu-pku/PaperBanana  
**Local path:** `external/upstreams/PaperBanana`  
**Integration mode:** Referenced  
**License:** Check upstream

**What we use:**  
The concept of automated diagram generation from structured research data, and the report outline automation pattern.

**What we adapted:**  
Our skills/diagram-generation/SKILL.md and the research output templates in docs/research-mode.md reflect these patterns. The diagram request format was inspired by PaperBanana's structured diagram specification approach.

**What we excluded:**  
Specific Python tooling and academic paper formatting code.

**Sync strategy:** Quarterly.

---

## agency-agents — `msitarzewski/agency-agents`

**URL:** https://github.com/msitarzewski/agency-agents  
**Local path:** `external/upstreams/agency-agents`  
**Integration mode:** Adapted  
**License:** Check upstream

**What we use:**  
The principle that agents are defined by their deliverables, not their personalities. Role quality criteria for judging whether an agent definition is complete and useful.

**What we adapted:**  
Our agents/ folder format draws directly on these patterns. Every agent file has: purpose, scope, responsibilities, inputs, outputs, tools, skills, handoffs, quality criteria, failure modes, escalation conditions.

**What we excluded:**  
Persona/personality descriptions that prioritize style over function.

**Sync strategy:** Quarterly.

---

## ClawTeam — `HKUDS/ClawTeam`

**URL:** https://github.com/HKUDS/ClawTeam  
**Local path:** `external/upstreams/ClawTeam`  
**Integration mode:** Referenced  
**License:** Check upstream

**What we use:**  
Team-based swarm execution model, convergence criteria design, and the concept of a unified entry point for swarm execution (one command to start the swarm).

**What we adapted:**  
Our docs/operating-model.md and scripts/run_swarm_cycle.sh operationalize these patterns. The convergence criteria (all tasks DONE + all gates pass) are directly inspired by ClawTeam's convergence design.

**What we excluded:**  
Framework-specific runtime code that requires specific infrastructure.

**Sync strategy:** Quarterly.

---

## What We Did Not Take From Any Upstream

- No code was vendored without explicit notation
- No platform-specific LLM integrations (we are model-agnostic in the templates)
- No agent "personalities" — all agents are function-defined
- No aspirational or motivational content in skill definitions
- No single-upstream design — all patterns are cross-validated across multiple upstreams

---

## Legal Notes

All upstream code remains subject to its own license. We:
1. Reference concepts and patterns (no license concern)
2. Do not vendor code without explicit attribution
3. Check licenses before any code vendoring (see `docs/licenses.md`)

See `upstreams/manifest.yaml` for license notes per upstream.
