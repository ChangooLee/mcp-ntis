# Agent Matrix

Maps project types to active agents, task types to primary agents, and agents to default skills.

---

## Project Type → Active Agents

| Project Type | Active Agents |
|---|---|
| `backend-service` | orchestrator, planner, architect, coder, tester, reviewer, debugger*, documenter, evaluator |
| `frontend-web` | orchestrator, planner, architect, coder, tester, reviewer, product-manager, documenter, evaluator |
| `full-stack` | All agents (red-team optional) |
| `data-etl` | orchestrator, planner, architect, coder, tester, evaluator, documenter |
| `ml-ai-system` | orchestrator, planner, architect, researcher, coder, evaluator, red-team, documenter |
| `research-report` | orchestrator, planner, researcher, documenter, evaluator, red-team* |
| `internal-docs` | orchestrator, planner, documenter, reviewer, product-manager |
| `automation-workflow` | orchestrator, planner, architect, coder, tester, documenter |
| `knowledge-system` | orchestrator, planner, retrieval-architect, knowledge-curator, researcher, evaluator, documenter |

\* Activated on-demand, not by default

---

## Task Type → Primary Agent

| Task Type | Primary Agent | Supporting Agents |
|---|---|---|
| Project planning and decomposition | planner | orchestrator |
| Architecture design | architect | planner |
| Interface specification | architect | coder |
| Code implementation | coder | reviewer |
| Unit test authoring | coder | tester |
| Integration test authoring | tester | coder |
| E2E test authoring | tester | — |
| Bug triage | debugger | coder |
| Bug fix | coder | debugger |
| Documentation | documenter | reviewer |
| Research | researcher | evaluator |
| Diagram generation | documenter / researcher | — |
| Quality gate evaluation | evaluator | tester, reviewer |
| Adversarial review | red-team | evaluator |
| Document index design | retrieval-architect | orchestrator |
| Document index build | knowledge-curator | retrieval-architect |
| Document retrieval | (any agent via skill) | knowledge-curator |
| Memory update | memory-curator | orchestrator |
| Retrospective | orchestrator | evaluator |
| Requirements clarification | product-manager | orchestrator |
| Prompt/instruction improvement | prompt-engineer | evaluator |
| Release packaging | release-manager | documenter |
| Project bootstrap | project-bootstrapper | orchestrator |

---

## Agent → Default Skills

| Agent | Primary Skill | Secondary Skills |
|---|---|---|
| orchestrator | swarm-orchestration | project-intake, task-routing |
| planner | goal-decomposition | implementation-planning |
| architect | implementation-planning | repo-recon, diagram-generation, doc-authoring |
| researcher | factual-research | diagram-generation, doc-authoring |
| coder | code-implementation | test-authoring, repo-recon |
| reviewer | (reads code, produces review) | code-implementation, test-authoring |
| tester | test-authoring | repo-recon |
| debugger | bug-triage | code-implementation, repo-recon |
| documenter | doc-authoring | diagram-generation, factual-research |
| memory-curator | memory-update | — |
| evaluator | quality-gate-design | retrospective-and-reflection, factual-research |
| red-team | adversarial-review | code-implementation, factual-research |
| release-manager | release-packaging | doc-authoring |
| retrieval-architect | (profile design, no build) | doc-authoring, factual-research |
| knowledge-curator | document-indexing | long-document-retrieval |
| product-manager | project-intake | doc-authoring, goal-decomposition |
| prompt-engineer | doc-authoring | retrospective-and-reflection, implementation-planning |
| project-bootstrapper | project-bootstrap | project-intake |

---

## Skill → Owning Agents

| Skill | Primary Owner(s) |
|---|---|
| project-intake | orchestrator, product-manager |
| repo-recon | orchestrator, architect, coder |
| goal-decomposition | planner |
| implementation-planning | planner, architect |
| task-routing | orchestrator |
| code-implementation | coder |
| test-authoring | tester, coder |
| bug-triage | debugger |
| doc-authoring | documenter |
| factual-research | researcher |
| memory-update | memory-curator |
| retrospective-and-reflection | orchestrator, evaluator |
| release-packaging | release-manager |
| diagram-generation | documenter, researcher |
| quality-gate-design | evaluator |
| swarm-orchestration | orchestrator |
| project-bootstrap | project-bootstrapper |
| adversarial-review | red-team |
| document-indexing | knowledge-curator |
| long-document-retrieval | knowledge-curator, (any agent) |

---

## Escalation Routing

| Escalation Type | Route To |
|---|---|
| Task ambiguity | orchestrator |
| Scope creep | orchestrator → product-manager |
| Architectural concern | architect |
| Security concern | orchestrator → operator |
| Human approval needed | orchestrator → operator |
| Budget exhausted | orchestrator → operator |
| Instruction conflict | orchestrator → operator |
| Research scope too large | researcher → orchestrator |
