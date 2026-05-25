# Hardening Plan

**Date:** 2026-04-15  
**Status:** Executed  
**Triggered by:** Post-build hardening pass

---

## Context

The master swarm project was built in a single session. This hardening pass inspects it for weaknesses and tightens it before first real use.

Key finding: Upstreams are not yet cloned (external/upstreams/ is empty). The upstream "PageIndex" referenced in the hardening spec does not exist in the manifest — it is treated here as a retrieval/document-indexing architectural pattern to implement natively.

---

## Hardening Priorities

### P0 — Critical (breaks usability)
1. AGENTS.md: missing human-approval timeout, vague conflict resolution, confidence threshold never wired
2. No document indexing/retrieval infrastructure despite retrieval being a core pattern
3. Missing escalation-model and convergence-model docs
4. Examples are skeletons — no state scaffolding or tasks

### P1 — High (weakens reusability)
5. skills/swarm-orchestration is too abstract — needs sub-step clarity
6. No red-team skill (agent references adversarial review but skill doesn't exist)
7. Missing runbooks: software-delivery, research-heavy, retrieval-heavy
8. state/indexes/ doesn't exist
9. Missing agents: retrieval-architect, knowledge-curator

### P2 — Medium (weakens depth)
10. Upstream notes are empty (upstreams/notes/*.md)
11. docs/decision-framework.md is missing
12. Cursor rules mention routing but don't reference agent-matrix
13. skills/index.md — not updated dynamically

### P3 — Low (polish)
14. Scripts missing safety guards for destructive operations
15. .gitignore doesn't handle state/indexes/
16. No version field in AGENTS.md

---

## Execution Order

1. Create hardening-audit.md (this plan)
2. Harden AGENTS.md
3. Add retrieval/indexing infrastructure
4. Add missing skills (document-indexing, long-document-retrieval, adversarial-review)
5. Add missing agents (retrieval-architect, knowledge-curator)
6. Add missing docs (decision-framework, escalation-model, convergence-model, knowledge-retrieval)
7. Add missing runbooks (software-delivery, research-heavy, retrieval-heavy)
8. Add knowledge-system example
9. Add upstream notes
10. Harden scripts
11. Fix .gitignore
12. Write reports/hardening-fixes.md
