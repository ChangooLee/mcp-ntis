# Architecture

This document describes the architectural design of the master swarm project itself.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MASTER SWARM PROJECT                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  CONTRACTS   │    │   SKILLS     │    │    AGENTS        │  │
│  │              │    │              │    │                  │  │
│  │ README.md    │    │ 17 skills    │    │ 16 specialist    │  │
│  │ AGENTS.md    │    │ skills/      │    │ agents/          │  │
│  │ .cursor/     │    │ index.md     │    │                  │  │
│  │   rules/     │    │              │    │                  │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────────┘  │
│         │                  │                    │              │
│         └──────────────────┼────────────────────┘              │
│                            ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    SWARM LOOP                           │   │
│  │                                                         │   │
│  │  Intake → Recon → Plan → Route → Execute → Verify →    │   │
│  │  Reflect → Update Memory → [Retry | Complete]          │   │
│  │                                                         │   │
│  │  Bounded by: retry budgets, max iterations,             │   │
│  │  stop conditions, approval gates                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                   │
│         ┌──────────────────┼────────────────────┐              │
│         ▼                  ▼                    ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │    STATE     │  │   MEMORY     │  │      DOCS           │  │
│  │              │  │              │  │                      │  │
│  │ state/tasks/ │  │ state/memory/│  │ docs/               │  │
│  │ state/runs/  │  │ project.md   │  │ docs/decisions/     │  │
│  │ state/       │  │ patterns/    │  │                      │  │
│  │  reflections │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Contracts

The contracts layer defines *how* the swarm operates.

- **README.md** — operator-facing project description
- **AGENTS.md** — machine-facing execution contract (authoritative)
- **.cursor/rules/*.mdc** — thin, durable behavioral rules for Cursor IDE

Design principle: Contracts are stable. They change only through the self-improvement cycle. They are not modified mid-run.

---

## Layer 2: Skills

The skills layer provides *what* can be done.

- 17 skill definitions in `skills/<name>/SKILL.md`
- Each skill has a defined interface (inputs, outputs, workflow)
- Skills are stateless — they take inputs and produce outputs
- Skills are invoked by agents, not directly by users

Design principle: Skills are modular and reusable. A skill that is useful in one project type should work in all project types.

---

## Layer 3: Agents

The agents layer defines *who* does the work.

- 16 specialist agent definitions in `agents/<name>.md`
- Each agent has a defined scope, skills, handoff targets, and escalation paths
- Agents are role-bearing — they have specific responsibilities and cannot do everything
- The orchestrator coordinates all agents but executes no tasks itself

Design principle: Agents are complementary without overlap. The routing table (agent-matrix.md) is the source of truth for who does what.

---

## Layer 4: Swarm Loop

The orchestration layer runs the work.

- Defined in `docs/operating-model.md`
- Scripted in `scripts/run_swarm_cycle.sh`
- Bounded by budgets and stop conditions
- State is written to `state/runs/<run-id>/`

Design principle: The loop is always bounded. There are no infinite loops. Human approval can pause but not bypass the loop.

---

## Layer 5: State and Memory

The persistence layer maintains context across tasks and runs.

- Task-level state in `state/tasks/<id>/`
- Run-level state in `state/runs/<run-id>/`
- Project memory in `state/memory/project.md`
- Pattern memory in `state/memory/patterns/`
- Decisions in `docs/decisions/`
- Reflections in `state/reflections/`

Design principle: Memory is layered by scope and lifetime. Nothing is lost silently — failures and patterns are explicitly recorded.

---

## Key Design Choices

### Choice 1: Markdown-first
All contracts, skills, agents, and docs are in Markdown. No special runtime required. Any agent (Claude, GPT, Gemini) that can read text can work with this system.

### Choice 2: Scripts for automation, Markdown for contracts
Bootstrap and run scripts are bash/PowerShell — they set up file structure and emit checklists. They do not run LLMs directly. The LLM reads the checklists.

### Choice 3: No single upstream dependency
We synthesize patterns from 12 upstreams rather than depending on any one. If an upstream changes or disappears, the project continues to work.

### Choice 4: Explicit over implicit
All decisions are logged. All routing is documented. All quality gates are defined. Nothing is inferred silently.

### Choice 5: Portable across project types
The same architecture handles backend services, research reports, data pipelines, and documentation. Project type determines agent team and quality gates — not architecture.

---

## File Naming Conventions

- Agent files: `agents/<name>.md` (lowercase, hyphenated)
- Skill folders: `skills/<name>/SKILL.md` (lowercase, hyphenated)
- Cursor rules: `.cursor/rules/<NN>-<name>.mdc` (numbered, hyphenated)
- Decision logs: `docs/decisions/<YYYY-MM-DD>-<slug>.md`
- Templates: `templates/<Name>.template.md` (PascalCase)
- Scripts: `scripts/<verb>_<noun>.<ext>` (lowercase, underscore-separated)

---

## Related Documents

- `docs/operating-model.md` — the swarm loop
- `docs/agent-matrix.md` — agent routing
- `docs/memory-model.md` — state and memory
- `docs/upstreams.md` — upstream integration
