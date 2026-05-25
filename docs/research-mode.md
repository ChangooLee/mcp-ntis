# Research Mode

This document describes how the master swarm project operates in research mode — for `research-report` project types and for research tasks within other project types.

Conceptually shaped by: AutoResearchClaw (aiming-lab), autoresearch (karpathy), PaperBanana (dwzhu-pku).

---

## When Research Mode Activates

1. `project_type: research-report` — the entire project is research-mode
2. A task of type `factual-research` is dispatched to the researcher agent
3. An architect or coder triggers research to evaluate technical alternatives

---

## Research Cycle

The research cycle is a bounded sub-loop within the main swarm loop:

```
Question formulation
  ↓
Scope definition (max iterations, sources, depth)
  ↓
Evidence gathering (iteration 1..n)
  ↓
Contradiction detection
  ↓
Synthesis (with confidence level)
  ↓
Evaluation (does synthesis answer the question?)
  ↓
If low confidence + budget available: refine question, gather more evidence
If budget exhausted or high confidence: produce output
```

**Max research iterations:** 5 (default). Override with `research.max_iterations` in AGENTS.md.

---

## Research Artifacts

| Artifact | Location | Purpose |
|---|---|---|
| Research brief | `state/tasks/<id>/outputs/research-brief.md` | Question, scope, constraints |
| Evidence log | `state/tasks/<id>/outputs/evidence-log.md` | Sources and extracted claims |
| Synthesis memo | `state/tasks/<id>/outputs/synthesis.md` | Answer + confidence + contradictions |
| Report outline | `state/tasks/<id>/outputs/report-outline.md` | For research-report projects |
| Diagram requests | `state/tasks/<id>/outputs/diagram-requests.md` | Specs for diagram-generation skill |

---

## Evidence Log Format

```markdown
# Evidence Log: <research question>
Date: <date>
Iteration: <n>

## Source: <name>
URL/Reference: <url or citation>
Date published: <date>
Author/Organization: <name>
Type: primary | benchmark | secondary | opinion
Credibility: high | medium | low
Relevant claims:
  - <claim 1>
  - <claim 2>
Assessment: <why this source is relevant or limited>

---

## Contradictions Found
- <claim A> (source: X) contradicts <claim B> (source: Y)
  Resolution: <how resolved or why unresolved>
```

---

## Synthesis Memo Format

```markdown
# Research Synthesis: <question>
Date: <date>
Research question: <specific, bounded question>
Iterations completed: <n>

## Answer
<direct answer to the question>

## Confidence
Level: high | medium | low
Reasoning: <why this confidence level>

## Key Evidence
- <claim> (source: <name>, date: <date>)

## Contradictions
- <what contradicts what>
  Resolution: <how or why unresolved>

## Limitations
- <what this research doesn't cover>
- <what additional evidence would increase confidence>

## Recommended Action
<concrete next step based on synthesis>
```

---

## Report Outline Format (research-report projects)

```markdown
# Report Outline: <project>
Date: <date>

## Executive Summary (to be written last)

## 1. Introduction
  - Background
  - Research question(s)
  - Scope and limitations

## 2. Methodology
  - Sources used
  - Evidence criteria
  - Synthesis approach

## 3. Findings
  - <Finding 1>
    - Evidence
    - Confidence
  - <Finding 2>

## 4. Analysis
  - Contradictions and resolutions
  - Limitations

## 5. Conclusions and Recommendations

## 6. References

## Appendix: Evidence Log (link to evidence-log.md)
```

---

## Diagram Generation in Research Mode

After synthesis, the researcher produces diagram requests:
- Architecture diagrams for technical research
- Flow diagrams for process research
- Comparison tables as diagrams
- Timeline diagrams for historical research

Format of diagram request:
```markdown
# Diagram Request
Type: architecture | flowchart | sequence | comparison
Title: <title>
Purpose: <what it should show>
Nodes:
  - <node>: <description>
Edges:
  - <from> → <to>: <relationship>
Format: mermaid | plantuml | ascii
Destination: <where to embed in report>
```

---

## Research Mode Quality Gates

| Gate | Pass Criteria |
|---|---|
| research-citations | Every claim in synthesis has a logged source |
| research-contradictions | All source contradictions are explicitly surfaced |
| research-synthesis | Question is answered with stated confidence level |

---

## Stop Conditions for Research Mode

Stop the research loop when:
- The synthesis confidence is high (> 0.8)
- The research iteration budget is exhausted
- The question cannot be answered with available sources (document this)
- The question scope needs to be reduced (flag to orchestrator)

---

## Related Documents

- `skills/factual-research/SKILL.md` — research execution
- `skills/diagram-generation/SKILL.md` — diagram outputs
- `templates/RETROSPECTIVE.template.md` — for research reflections
- `agents/researcher.md` — researcher agent definition
