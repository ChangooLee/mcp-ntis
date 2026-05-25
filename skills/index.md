# Skills Index

All available skills in this master project. Invoke by referencing the skill ID in a task brief or agent invocation.

---

## Skill Catalog

| ID | Title | Purpose | Primary Users |
|---|---|---|---|
| `project-intake` | Project Intake | Gather and structure project context from README + AGENTS | orchestrator |
| `repo-recon` | Repository Reconnaissance | Map existing repo structure, stack, conventions | orchestrator, coder, architect |
| `goal-decomposition` | Goal Decomposition | Break high-level goals into executable task graphs | planner, orchestrator |
| `implementation-planning` | Implementation Planning | Create step-by-step plans for medium/large tasks | planner, architect |
| `task-routing` | Task Routing | Assign tasks to agents and confirm skill availability | orchestrator |
| `code-implementation` | Code Implementation | Write code that meets acceptance criteria | coder |
| `test-authoring` | Test Authoring | Write tests for features and bug fixes | tester, coder |
| `bug-triage` | Bug Triage | Root cause analysis and targeted fix brief | debugger, coder |
| `doc-authoring` | Documentation Authoring | Write accurate, audience-appropriate documentation | documenter |
| `factual-research` | Factual Research | Evidence-based research with contradiction detection | researcher |
| `memory-update` | Memory Update | Persist project state and patterns after task/run | memory-curator |
| `retrospective-and-reflection` | Retrospective and Reflection | Post-run analysis and improvement proposals | orchestrator, evaluator |
| `release-packaging` | Release Packaging | Package deliverables for operator handoff | release-manager |
| `diagram-generation` | Diagram Generation | Generate architecture, flow, and data diagrams | documenter, researcher |
| `quality-gate-design` | Quality Gate Design | Define project-specific quality gates | evaluator, orchestrator |
| `swarm-orchestration` | Swarm Orchestration | Run the multi-agent swarm loop | orchestrator |
| `project-bootstrap` | Project Bootstrap | Initialize a new project from this master template | project-bootstrapper |
| `adversarial-review` | Adversarial Review | Red-team analysis: injection, trust violations, unsupported claims | red-team, evaluator |
| `document-indexing` | Document Indexing | Build and refresh document indexes from source inventories | knowledge-curator |
| `long-document-retrieval` | Long Document Retrieval | Query indexes and retrieve relevant chunks for task context | any agent with retrieval needs |

---

## Skill Selection Guide

**Starting a new project:**
1. `project-bootstrap` → `project-intake` → `repo-recon` (if existing code)

**Planning:**
2. `goal-decomposition` → `implementation-planning` → `task-routing`

**Execution:**
3. `code-implementation` + `test-authoring` (in parallel or sequence)

**Quality:**
4. `quality-gate-design` → validate after completion

**Research projects:**
`project-intake` → `factual-research` → `diagram-generation` → `doc-authoring`

**Knowledge/retrieval projects:**
`document-indexing` (build) → `long-document-retrieval` (query) → `adversarial-review` (validate)

**When something goes wrong:**
`bug-triage` → `code-implementation` → `test-authoring`

**After every run:**
`retrospective-and-reflection` → `memory-update`

**When ready to deliver:**
`release-packaging`

---

## Skill-to-Agent Matrix

| Agent | Primary Skills |
|---|---|
| orchestrator | swarm-orchestration, task-routing, project-intake |
| planner | goal-decomposition, implementation-planning |
| architect | implementation-planning, repo-recon |
| researcher | factual-research, diagram-generation |
| coder | code-implementation, test-authoring |
| tester | test-authoring |
| debugger | bug-triage |
| documenter | doc-authoring, diagram-generation |
| memory-curator | memory-update |
| evaluator | quality-gate-design, retrospective-and-reflection |
| release-manager | release-packaging |
| project-bootstrapper | project-bootstrap |
| red-team | adversarial-review |
| knowledge-curator | document-indexing, long-document-retrieval |
| retrieval-architect | (designs profile; does not execute) |
