# Project Types

This document defines the supported project types, their characteristics, agent teams, quality gates, and routing rules.

---

## How Project Types Work

1. The operator specifies `project_type` in AGENTS.md (or it is inferred from README.md)
2. The orchestrator looks up the type here
3. The orchestrator activates the specified agent team
4. The evaluator applies the specified quality gates
5. The planner uses type-specific decomposition patterns

---

## Project Type: `backend-service`

**Description:** API services, microservices, server-side systems, CLIs

**Characteristics:**
- Has public interfaces (HTTP, gRPC, CLI, message queue)
- Requires testing at unit and integration level
- Has deployment and configuration concerns
- Documentation is primarily for developers/operators

**Agent Team:**
- orchestrator (always)
- planner
- architect
- coder (primary executor)
- tester
- reviewer
- debugger (on-demand)
- documenter
- evaluator

**Quality Gates:**
- universal-completeness
- universal-correctness
- universal-handoff
- sw-test-coverage
- sw-no-regressions
- sw-api-docs

**Decomposition Patterns:**
- Design interfaces first (architect) before implementation (coder)
- Test authoring task should follow implementation task in graph
- Docs task can run in parallel with testing

---

## Project Type: `frontend-web`

**Description:** Web applications, SPAs, React/Vue/Next apps, static sites

**Characteristics:**
- User-facing interface
- Browser compatibility concerns
- UI state management
- Accessibility considerations

**Agent Team:**
- orchestrator
- planner
- architect
- coder
- tester
- reviewer
- product-manager
- documenter
- evaluator

**Quality Gates:**
- universal-completeness
- universal-correctness
- universal-handoff
- sw-test-coverage
- sw-no-regressions
- (accessibility check: manual or tooled)

---

## Project Type: `full-stack`

**Description:** Projects that have both frontend and backend components

**Characteristics:** All of the above

**Agent Team:** Full team (all agents except red-team unless security is in scope)

**Quality Gates:** All software gates + any project-specific gates defined in AGENTS.md

---

## Project Type: `data-etl`

**Description:** Data pipelines, ETL systems, data processing tooling

**Characteristics:**
- Operates on data (potentially large volumes)
- Has schema and data quality concerns
- Must be reproducible
- Has idempotency requirements

**Agent Team:**
- orchestrator
- planner
- architect
- coder
- tester
- evaluator
- documenter

**Quality Gates:**
- universal-completeness
- universal-correctness
- universal-handoff
- data-schema-valid
- data-quality
- data-reproducible

**Decomposition Patterns:**
- Schema definition before pipeline implementation
- Data quality gate definition before any data processing task

---

## Project Type: `ml-ai-system`

**Description:** ML model development, AI system implementation, model serving

**Characteristics:**
- Has evaluation metrics, not just pass/fail tests
- Requires experiment tracking
- Has bias and distribution concerns
- Reproducibility is a research-grade requirement

**Agent Team:**
- orchestrator
- planner
- architect
- researcher
- coder
- evaluator
- red-team (for adversarial robustness)
- documenter

**Quality Gates:**
- universal-completeness
- universal-correctness
- universal-handoff
- sw-test-coverage (for the serving infrastructure)
- data-reproducible (for training pipelines)
- research-synthesis (for model evaluation reports)
- (red-team report required before release)

---

## Project Type: `research-report`

**Description:** Research, literature review, paper generation, technical reports

**Characteristics:**
- Knowledge-intensive, not code-intensive
- Output is documents and diagrams
- Quality is measured by evidence quality and synthesis clarity
- May require multiple research iterations

**Agent Team:**
- orchestrator
- planner
- researcher (primary executor)
- documenter
- evaluator
- red-team (for claim validation)

**Quality Gates:**
- universal-completeness
- universal-correctness
- universal-handoff
- research-citations
- research-contradictions
- research-synthesis

**Decomposition Patterns:**
- Start with question formulation task
- Evidence gathering can be parallelized by subtopic
- Synthesis after evidence gathering
- Documentation after synthesis
- Diagram generation alongside documentation

---

## Project Type: `internal-docs`

**Description:** Internal wikis, runbooks, onboarding guides, architecture documentation

**Characteristics:**
- Documentation-heavy
- Audience is internal team members
- May reference existing systems
- Accuracy is critical (wrong docs are worse than no docs)

**Agent Team:**
- orchestrator
- planner
- documenter (primary executor)
- reviewer
- product-manager

**Quality Gates:**
- universal-completeness
- universal-correctness
- universal-handoff
- docs-links-valid
- docs-accuracy

---

## Project Type: `automation-workflow`

**Description:** Workflow automation, system integrations, scripting, bots

**Characteristics:**
- Interacts with external systems
- Has side effects (state changes in external systems)
- Must be idempotent or explicitly not
- Rollback and error handling are critical

**Agent Team:**
- orchestrator
- planner
- architect
- coder
- tester
- documenter

**Quality Gates:**
- universal-completeness
- universal-correctness
- universal-handoff
- sw-test-coverage
- auto-integration-tested
- auto-idempotent
- auto-rollback

---

## Project Type: `knowledge-system`

**Description:** Document corpora, knowledge bases, searchable archives, retrieval-augmented systems

**Characteristics:**
- Large volume of source documents (> 20, often > 100)
- Retrieval quality is the primary deliverable metric
- Index freshness and accuracy are ongoing concerns
- Users/agents query the system rather than reading raw documents
- Requires document-indexing infrastructure

**Agent Team:**
- orchestrator
- planner
- retrieval-architect (index design)
- knowledge-curator (index build and maintenance)
- researcher (source evaluation)
- evaluator (retrieval quality)
- documenter

**Quality Gates:**
- universal-completeness
- universal-correctness
- universal-handoff
- retrieval-score-threshold (> 0.6 on test queries)
- retrieval-coverage (< 30% sources skipped)
- index-manifest-complete
- docs-accuracy (for any documentation produced)

**Decomposition Patterns:**
- Design retrieval profile first (retrieval-architect) before building (knowledge-curator)
- Source inventory and retrieval profile must be complete before index build starts
- Test retrieval queries must be defined before evaluating index quality
- Documentation of query patterns should accompany every index build

**Indexing:**
`indexing: required` — always enable document indexing for this type.

---

## Adding a New Project Type

1. Add an entry to this file following the format above
2. Define: description, characteristics, agent team, quality gates, decomposition patterns
3. Add routing rule to `.cursor/rules/90-project-type-routing.mdc`
4. Update `docs/agent-matrix.md`
5. Create an example in `examples/<type>/`
6. Log the decision in `docs/decisions/`
