# Runbook: Research-Heavy Project

Step-by-step guide for running a `research-report` or `ml-ai-system` project through the swarm. These projects produce knowledge artifacts (reports, analysis, evaluations) rather than software.

---

## Prerequisites

- README.md written with a clear research question or goal
- AGENTS.md configured with `project_type: research-report` (or `ml-ai-system`)
- `./scripts/bootstrap.sh` has been run

---

## Step 1: Research Scoping

The planner runs `goal-decomposition` to define the research scope:

1. Identify the primary research question
2. Identify sub-questions (decompose the question into answerable parts)
3. Identify required evidence types (papers, data, benchmarks, expert opinion)
4. Identify scope constraints (time, sources, budget)
5. Flag any parts of the question that are unanswerable given constraints

**Output:** Task graph with discrete research subtasks, each answering one sub-question.

**Human review point:** Confirm the research question decomposition before proceeding. A badly scoped question wastes research cycles.

---

## Step 2: Source Identification

Before the researcher starts writing, identify available sources:

1. What databases/archives are accessible? (ArXiv, Semantic Scholar, internal wikis)
2. What existing documents exist in `external/upstreams/` that are relevant?
3. Are there more than 10 relevant documents? If yes, consider indexing (see Step 2b)

**Step 2b — Optional: Build a Document Index**

If the research involves > 10 documents, use the indexing infrastructure:

```bash
./scripts/build_document_index.sh --index-id research-<topic>
# Edit the generated source-inventory.yaml, then:
./scripts/run_swarm_cycle.sh
```

The knowledge-curator agent will build the index. The researcher then uses `long-document-retrieval` instead of reading documents directly.

---

## Step 3: Research Execution (Bounded)

The researcher runs `factual-research` for each sub-question.

**Research loop bounds (from AGENTS.md):**
- Max iterations per sub-question: 5 (configurable via `research.max_iterations`)
- Per-task retry budget: 3

**Each research cycle produces:**
- A finding with evidence
- A confidence score (0–1)
- Source citations
- Contradictions detected (if any)

**If contradictions are found:**
- Document both positions with sources
- Do not pick a side without evidence
- Flag to the evaluator for adjudication

---

## Step 4: Cross-Verification

The evaluator verifies research outputs before they are used in the final report:

1. Checks claim-to-source traceability (every claim has a citation)
2. Checks for unsupported generalizations
3. Flags contradictions within the research output
4. Assigns a confidence score to each section

**If evaluator confidence < 0.7 on a section:**
- Return to the researcher with specific gaps to fill
- Allow up to 2 retries (gate retry budget)
- After 2 retries: mark the section as "low confidence" and include it with a caveat

---

## Step 5: Adversarial Review

For reports that will influence decisions, run the red-team agent:

```yaml
# In state/tasks/T_redteam/brief.md
agent: red-team
skill: adversarial-review
target: state/tasks/T_report-draft/outputs/report-draft.md
focus: [unsupported-claims, source-cherry-picking, scope-misrepresentation]
```

The red-team produces:
- A severity-classified list of findings
- Specific claims to revise or remove
- Sources that should be added to balance the analysis

**Critical or high-severity findings must be resolved before convergence.**

---

## Step 6: Diagram Generation

For reports requiring visual aids:

```yaml
agent: documenter
skill: diagram-generation
input: state/tasks/T_research/outputs/
output_types: [architecture-diagram, flow-diagram, data-chart]
```

Diagrams are written to `state/tasks/T_diagrams/outputs/` and referenced in the final report.

---

## Step 7: Report Authoring

The documenter runs `doc-authoring` to assemble the final report:

**Input:**
- Research findings from each sub-task
- Evaluator confidence scores
- Diagram outputs
- Red-team review findings and resolutions

**Output structure:**
```
state/tasks/T_report/outputs/
  report.md          ← main report
  appendix.md        ← detailed evidence tables, raw data
  sources.md         ← full bibliography
  confidence.md      ← per-section confidence scores
```

---

## Step 8: Quality Gate Check

```bash
./scripts/run_quality_gates.sh
```

For research projects, gates that must pass:
- `research-citations` — all claims are cited
- `research-contradictions-surfaced` — known contradictions are documented
- `research-scope-respected` — output stays within defined scope
- `universal-handoff` — report is readable by the intended audience

---

## Step 9: Reflection

After the run:

1. What sub-questions were well-answered vs. under-answered?
2. What sources were most useful? (inform future retrieval profiles)
3. What would improve the research process for this type of question?
4. Should any patterns be added to `state/memory/patterns/`?

---

## Common Problems

### Researcher Is Looping Without Converging

Research loops without producing findings usually mean the question is too broad.

1. Check `state/runs/<run-id>/cycle-log.md` for the cycle pattern
2. Read the researcher's task log — is it looking for sources that don't exist?
3. Narrow the sub-question scope
4. If the question is genuinely unanswerable with available sources, mark it as such and move on

### Contradicting Sources

Research often surfaces conflicting findings. Correct response:

1. Document both positions explicitly
2. Evaluate the quality of evidence on each side
3. Report the contradiction clearly in the final report — do not suppress it
4. Let the human operator decide which position to act on

### Report Is Too Long

The evaluator will flag this as a quality issue. The documenter should:

1. Move supporting detail to `appendix.md`
2. Summarize each section to ≤ 300 words
3. Ensure the executive summary covers the decision-relevant content

### Low Confidence Sections

If a section cannot reach confidence ≥ 0.7 after 2 evaluator retries:

1. Include the section with a visible caveat: `[LOW CONFIDENCE — insufficient evidence]`
2. Document what additional evidence would raise confidence
3. Proceed to convergence — do not block the run on unanswerable sub-questions

---

## Related Documents

- `docs/research-mode.md` — research mode detail
- `docs/knowledge-retrieval.md` — when and how to use document indexing
- `docs/quality-gates.md` — research-specific quality gates
- `docs/runbook-retrieval-heavy.md` — if your research uses a large document corpus
- `skills/factual-research/SKILL.md` — research skill interface
- `skills/adversarial-review/SKILL.md` — red-team skill interface
