# Knowledge Retrieval

This document defines the document indexing and retrieval architecture used when projects operate on large document corpora.

---

## When Retrieval Is Needed

Retrieval is required when:
- A project has > 5 source documents that will be referenced repeatedly
- A research project has > 10 evidence sources
- A knowledge-system project type is used
- `indexing: required` is set in AGENTS.md project config

Retrieval is optional when:
- A project has 2–5 documents (read directly)
- An internal-docs project has < 20 files

Retrieval is disabled when:
- `indexing: disabled` is set in AGENTS.md

---

## Architecture

```
Source documents
    ↓
[retrieval-architect] designs profile
    ↓
[knowledge-curator] builds index
    ↓
state/indexes/<index-id>/
    ↓
[long-document-retrieval skill] retrieves chunks
    ↓
Agent task with targeted context
```

---

## Index Lifecycle

| Phase | Agent | Skill |
|---|---|---|
| Design | retrieval-architect | implementation-planning |
| Source inventory | retrieval-architect | repo-recon |
| Build | knowledge-curator | document-indexing |
| Validate | knowledge-curator | long-document-retrieval (test query) |
| Use | any agent | long-document-retrieval |
| Refresh | knowledge-curator | document-indexing (incremental) |
| Archive | memory-curator | — |

---

## Index Profile Fields

Every index has a `retrieval-profile.yaml`:

```yaml
index_id: <id>
search_mode: keyword   # keyword | semantic | hybrid
chunk_size: 500        # max tokens per chunk (smaller = more precise; larger = more context)
overlap: 50            # token overlap between adjacent chunks
top_k: 5               # default results per query
freshness_threshold_days: 7
filters_available:
  - tags
  - source_id
  - date_range
boost_fields:
  - title: 2.0
  - tags: 1.5
  - content: 1.0
notes: ""
```

**Choosing chunk_size:**
- Technical docs with dense information: 300–400 tokens
- Narrative documents: 500–600 tokens
- Legal/formal documents: 400–500 tokens

**Choosing search_mode:**
- `keyword`: fast, exact match, works without an embedding model
- `semantic`: requires embedding model, better recall for paraphrased queries
- `hybrid`: best of both, requires embedding model

---

## Source Inventory Format

```yaml
index_id: <id>
created: <date>
sources:
  - id: src001
    path: docs/architecture.md          # local path
    type: markdown                      # markdown | pdf | text | html | code
    priority: high                      # high | medium | low
    tags: [architecture, system-design]
    include_sections: []                # empty = all sections
    exclude_sections: [Appendix]
  - id: src002
    url: https://example.com/spec.pdf   # remote URL
    type: pdf
    priority: medium
    tags: [specification]
```

---

## Retrieval Quality Evaluation

After building an index, test it with 3 representative queries:
1. A specific factual query (expected: high relevance, precise chunk)
2. A broad topic query (expected: diverse chunks from multiple sources)
3. A negative query (a topic NOT in the corpus — expected: low scores, no false positives)

**Quality thresholds:**
- Top-1 relevance score > 0.7: good
- Top-1 score 0.5–0.7: acceptable (refine query before using)
- Top-1 score < 0.5: poor (rebuild with different chunking or search_mode)

---

## Retrieval in Research Mode

Research projects use retrieval as a primary evidence-gathering mechanism:

1. Build index from known sources (document-indexing)
2. For each research question, run targeted queries (long-document-retrieval)
3. Log retrieved chunks in evidence-log.md with source attribution
4. Cross-reference retrieved evidence across chunks from different sources
5. Flag contradictions found through retrieval

---

## Project Type Defaults

| Project type | Default indexing | Default chunk_size | Default top_k |
|---|---|---|---|
| research-report | required if > 10 sources | 400 | 5 |
| internal-docs | required if > 20 docs | 500 | 3 |
| knowledge-system | always required | 400 | 8 |
| backend-service | disabled | — | — |
| data-etl | disabled | — | — |
| ml-ai-system | optional (papers/specs) | 400 | 5 |

---

## Adding a New Source to an Existing Index

1. Add the source to `state/indexes/<id>/source-inventory.yaml`
2. Request the knowledge-curator to run an incremental refresh
3. Verify the new source appears in the build-log.md
4. Run a test query that should surface the new source

---

## Related Documents

- `skills/document-indexing/SKILL.md`
- `skills/long-document-retrieval/SKILL.md`
- `agents/retrieval-architect.md`
- `agents/knowledge-curator.md`
- `state/indexes/README.md`
- `AGENTS.md §25`
