---
id: document-indexing
title: Document Indexing
version: 1.0
purpose: Ingest, chunk, metadata-tag, and index a document corpus so that it can be efficiently retrieved by agents in later tasks. Produces a structured index artifact and a retrieval profile.
when_to_use:
  - Before any task that requires reading > 5 documents from a corpus
  - At project start for research-report, knowledge-system, and internal-docs projects
  - When source documents have changed significantly since last index build
  - When the retrieval-architect specifies a new index profile
when_not_to_use:
  - For a single document (read it directly)
  - When the corpus is < 5 documents and < 50 pages total
  - When indexing: disabled is set in AGENTS.md project config
required_inputs:
  - Source document paths or URLs (source-inventory.yaml)
  - Index profile (from retrieval-architect, or use default from state/indexes/default-profile.yaml)
outputs:
  - state/indexes/<index-id>/manifest.yaml (what was indexed)
  - state/indexes/<index-id>/chunks/ (chunked document segments)
  - state/indexes/<index-id>/metadata.yaml (per-document metadata)
  - state/indexes/<index-id>/retrieval-profile.yaml (how to query this index)
  - state/indexes/<index-id>/build-log.md (what was indexed, what was skipped, errors)
related_docs:
  - docs/knowledge-retrieval.md
  - skills/long-document-retrieval/SKILL.md
  - agents/retrieval-architect.md
  - agents/knowledge-curator.md
  - AGENTS.md §25
escalation: If source documents are inaccessible (permission errors, broken links, encrypted), log each failure and proceed with available sources. If > 30% of sources are inaccessible, escalate to the orchestrator before completing the index.
---

# Skill: Document Indexing

## Purpose

Produce a structured index of a document corpus that enables targeted retrieval, reducing the cost and latency of reading large document sets in later tasks.

## Workflow

### Step 1 — Load source inventory

Read the source inventory file. If none exists, create one:

`state/indexes/<index-id>/source-inventory.yaml`:
```yaml
index_id: <index-id>
created: <date>
sources:
  - id: src001
    path: docs/architecture.md
    type: markdown
    priority: high
    tags: [architecture, system-design]
  - id: src002
    url: https://example.com/spec.pdf
    type: pdf
    priority: medium
    tags: [specification]
```

### Step 2 — Validate source access

For each source:
- Confirm it exists (local) or is reachable (remote)
- Record file size and modification date
- Flag inaccessible sources in build-log.md

### Step 3 — Chunk documents

Chunk each document into segments suitable for retrieval:

**Chunking rules:**
- Markdown: split at `##` headings (preserve heading as chunk title)
- PDF: split at page boundaries (or paragraph breaks for PDFs > 20 pages)
- Plain text: split at double newlines, max 500 tokens per chunk
- Code: split at function/class boundaries, never mid-function

Each chunk:
```yaml
chunk_id: src001-chunk-003
source_id: src001
title: "Architecture — Layer 2: Skills"
content: "..."
tokens: 380
page_start: 12
tags: [architecture, skills, layer]
```

### Step 4 — Generate metadata

For each source document, record:
```yaml
doc_id: src001
path: docs/architecture.md
title: "Architecture"
summary: "One-paragraph summary of document content"
chunk_count: 8
tags: [architecture, system-design]
last_modified: 2026-04-15
indexed_at: 2026-04-15T14:00:00Z
```

### Step 5 — Write retrieval profile

`state/indexes/<index-id>/retrieval-profile.yaml`:
```yaml
index_id: <index-id>
search_mode: keyword     # keyword | semantic | hybrid
chunk_size: 500          # max tokens per chunk
overlap: 50              # overlap tokens between adjacent chunks
top_k: 5                 # default results per query
filters_available:
  - tags
  - source_id
  - date_range
boost_fields:
  - title: 2.0
  - tags: 1.5
  - content: 1.0
freshness_threshold_days: 7   # rebuild if sources older than this
```

### Step 6 — Write build log

`state/indexes/<index-id>/build-log.md`:
```markdown
# Index Build Log: <index-id>
Date: <date>
Sources attempted: <n>
Sources indexed: <n>
Sources skipped: <n> (reason: <list>)
Total chunks: <n>
Total tokens: <n>
Build duration: <hh:mm:ss>

## Skipped sources
- <path>: <reason>

## Warnings
- <warning if any>
```

### Step 7 — Write index manifest

`state/indexes/<index-id>/manifest.yaml`:
```yaml
index_id: <index-id>
status: complete | partial | failed
built_at: <timestamp>
source_count: <n>
chunk_count: <n>
retrieval_profile: state/indexes/<index-id>/retrieval-profile.yaml
metadata: state/indexes/<index-id>/metadata.yaml
chunks_dir: state/indexes/<index-id>/chunks/
```

## Refresh Policy

- **Trigger:** source file modified date > `freshness_threshold_days`
- **Action:** rebuild affected sources only (incremental refresh)
- **Full rebuild:** when retrieval-profile.yaml changes

## Do

- Record every skipped source with the reason
- Generate summaries for each document (used by retrieval ranking)
- Keep chunk size consistent within an index
- Tag chunks with source metadata for filtering

## Don't

- Don't chunk mid-sentence or mid-code-block
- Don't index credentials, tokens, or private keys found in documents
- Don't build a new index if an up-to-date one already exists
- Don't proceed if > 30% of sources are inaccessible
