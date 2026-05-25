---
id: long-document-retrieval
title: Long Document Retrieval
version: 1.0
purpose: Retrieve the most relevant document chunks from a pre-built index to answer a specific question or inform a specific task, without reading entire documents.
when_to_use:
  - When a task requires information from a corpus of > 5 documents
  - When full document reading would exceed practical context limits
  - For research tasks drawing on an indexed evidence corpus
  - When the knowledge-curator or retrieval-architect specifies retrieval is needed
when_not_to_use:
  - When no index exists (build one first using document-indexing skill)
  - When the entire document is needed (read it directly)
  - For documents < 2 pages (read directly, retrieval overhead not worth it)
required_inputs:
  - state/indexes/<index-id>/manifest.yaml (the index to query)
  - Retrieval query (specific question or task description)
  - Optional: tag filters, date range, source filters
outputs:
  - state/tasks/<id>/outputs/retrieval-results.yaml (ranked chunks with metadata)
  - state/tasks/<id>/outputs/retrieval-log.md (query, parameters, result count)
related_docs:
  - docs/knowledge-retrieval.md
  - skills/document-indexing/SKILL.md
  - agents/retrieval-architect.md
  - AGENTS.md §25
escalation: If the index is stale (sources modified after last build) and freshness is critical, pause retrieval and request a knowledge-curator to rebuild the index before proceeding.
---

# Skill: Long Document Retrieval

## Purpose

Extract targeted information from a large document corpus without reading every document, using the pre-built index to surface the most relevant chunks.

## Workflow

### Step 1 — Load index manifest

Confirm the index exists and is not stale:
```bash
# Check: state/indexes/<index-id>/manifest.yaml
# Verify: status == complete
# Verify: built_at is within freshness_threshold_days
```

If stale: log a warning and either proceed (if freshness is not critical) or request a rebuild.

### Step 2 — Formulate retrieval query

Transform the task need into a precise retrieval query:

**Good query:** "JWT token expiry validation edge cases"  
**Bad query:** "auth stuff"

**Query components:**
- Primary terms: the core topic (2-5 words)
- Context terms: related concepts that help rank results
- Negative terms: concepts to exclude if index has noise

### Step 3 — Apply filters

From the retrieval profile and task context, specify:
```yaml
query: "JWT token expiry validation"
top_k: 5
filters:
  tags: [auth, security, jwt]
  source_ids: [src001, src002]  # optional: restrict to specific sources
  date_range:
    after: 2024-01-01
boost: title      # prefer chunks where query terms appear in title
```

### Step 4 — Retrieve and rank chunks

For each result chunk, record:
```yaml
rank: 1
chunk_id: src001-chunk-007
source_id: src001
source_path: docs/auth-design.md
title: "JWT Validation — Expiry Edge Cases"
relevance_score: 0.92
content: "..."  # the actual chunk text
tags: [auth, jwt, security]
```

### Step 5 — Evaluate result quality

Before using retrieved chunks:
- Do the top results actually answer the query?
- Is the relevance_score reasonable (> 0.6 for top result)?
- Are results from diverse sources or all from one?

If quality is poor:
- Refine query (add context terms, remove overly broad terms)
- Adjust top_k (try higher to see more results)
- Try with different filters

### Step 6 — Write retrieval results

`state/tasks/<id>/outputs/retrieval-results.yaml`:
```yaml
query: "JWT token expiry validation"
index_id: <index-id>
retrieved_at: <timestamp>
results_count: 5
results:
  - rank: 1
    chunk_id: src001-chunk-007
    source_path: docs/auth-design.md
    title: "JWT Validation — Expiry Edge Cases"
    relevance_score: 0.92
    content: "..."
```

`state/tasks/<id>/outputs/retrieval-log.md`:
```markdown
# Retrieval Log: <task-id>
Date: <date>
Query: <query>
Index: <index-id>
Filters applied: <filters>
Results returned: <n>
Top result score: <score>
Quality assessment: good | acceptable | poor
Refinements made: <if any>
```

### Step 7 — Provide retrieved context to task

Pass the top-k chunks as context to the executing agent. The agent reads retrieved chunks, not the full documents.

**Cite sources in all outputs:** Every claim derived from retrieval must include the source_path and chunk_id.

## Retrieval Strategies by Task Type

| Task | Strategy |
|---|---|
| Answer a specific factual question | Top-3 chunks, high relevance threshold (> 0.7) |
| Survey a topic | Top-10 chunks, diverse sources |
| Find contradictions | Run 2+ queries from different angles, compare |
| Verify a claim | Targeted query + negative query ("claim is wrong") |
| Generate a summary | Top-5 chunks per subtopic |

## Do

- Always cite the source chunk for retrieved information
- Evaluate result quality before using — don't trust low-relevance results
- Log every retrieval query for audit and debugging

## Don't

- Don't use retrieval results as ground truth without verifying against source
- Don't mix chunks from different index builds (different freshness)
- Don't retrieve if the index is known to be corrupt or incomplete
