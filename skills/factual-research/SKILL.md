---
id: factual-research
title: Factual Research
version: 1.0
purpose: Systematically gather, evaluate, and synthesize information to answer a research question or inform a project decision.
when_to_use:
  - When a decision depends on information not yet available in the repo
  - For research-report project types
  - When evaluating technical options that require external evidence
  - Before recommending a significant architectural choice
when_not_to_use:
  - For information that is already in the repo or clearly derivable from the code
  - When the decision has already been made (use doc-authoring instead)
  - For pure creative generation (no research needed)
required_inputs:
  - Research question (specific and bounded)
  - Scope constraints (sources to use, time horizon, depth)
outputs:
  - state/tasks/<id>/outputs/research-brief.md (question + scope)
  - state/tasks/<id>/outputs/evidence-log.md (sources + extracts)
  - state/tasks/<id>/outputs/synthesis.md (answer + confidence)
related_docs:
  - docs/research-mode.md
  - AGENTS.md §6
escalation: If sources directly contradict each other on a material point, flag the contradiction explicitly in the synthesis — do not silently resolve it.
---

# Skill: Factual Research

## Purpose

Produce a synthesis that answers the research question with specific evidence, explicit confidence levels, and documented contradictions.

## Workflow

### Step 1 — Frame the research question

A good research question is:
- Specific: "What are the performance tradeoffs between Redis Cluster and Redis Sentinel for our workload profile?"
- Bounded: has a clear answer space
- Falsifiable: evidence can confirm or deny candidate answers

Bad question: "Tell me about databases."

### Step 2 — Define scope

Before gathering evidence:
- What sources are in scope (documentation, papers, benchmarks, code)?
- What time horizon is relevant (last 2 years, all time)?
- What depth is needed (overview, detailed, exhaustive)?
- What is the max iteration budget for this research? (default: 5)

### Step 3 — Gather evidence

For each source:
1. Record: source name/URL, date, author/organization, relevance
2. Extract: specific claims relevant to the question
3. Assess: credibility (primary source, secondary, opinion, benchmark)

Log to `state/tasks/<id>/outputs/evidence-log.md`:
```markdown
## Source: <name>
URL/Reference: <url or citation>
Date: <date>
Type: primary | benchmark | secondary | opinion
Relevant claims:
  - <claim 1>
  - <claim 2>
Credibility assessment: high | medium | low
```

### Step 4 — Detect contradictions

After gathering evidence:
- List any direct contradictions between sources
- For each contradiction: note both claims, note which source is more credible, and why

### Step 5 — Synthesize

Write `state/tasks/<id>/outputs/synthesis.md`:
```markdown
# Research Synthesis: <question>
Date: <date>
Question: <specific question>
Answer: <direct answer>
Confidence: high | medium | low
Reasoning: <why this answer>
Key evidence:
  - <claim> (source: <name>)
Contradictions identified:
  - <what contradicts what>
  - Resolution: <how resolved or why unresolved>
Limitations:
  - <what this research doesn't cover>
Recommended action:
  - <concrete recommendation based on synthesis>
```

### Step 6 — Iterate if needed

If the synthesis confidence is low and the question is material:
- Identify what additional evidence would increase confidence
- Gather it (within budget)
- Re-synthesize

## Do

- Frame the question before gathering evidence
- Log sources as you find them
- Report contradictions explicitly
- State your confidence level

## Don't

- Don't gather evidence without a specific question
- Don't synthesize without logging sources
- Don't resolve contradictions silently — surface them
- Don't claim high confidence without multiple corroborating sources
