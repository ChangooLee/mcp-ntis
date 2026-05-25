# Runbook: Retrieval-Heavy Project

Step-by-step guide for projects that require searching or synthesizing information from a large document corpus. This applies to `knowledge-system` projects and any project with `indexing: required` in AGENTS.md.

---

## When This Runbook Applies

Use this runbook when:
- Your project has > 10 source documents that agents need to read
- You are building a `knowledge-system`
- Your `research-report` draws from a large private document corpus
- AGENTS.md sets `indexing: required`

If your project has ≤ 10 documents, agents can read them directly — no indexing needed.

---

## Prerequisites

- README.md and AGENTS.md complete
- Source documents are accessible on disk (or paths to remote sources are known)
- `./scripts/bootstrap.sh` has been run

---

## Step 1: Design the Retrieval Profile

The retrieval-architect designs the indexing strategy before any documents are indexed.

**The retrieval-architect produces:**
- `state/indexes/<index-id>/source-inventory.yaml` — which documents to index
- `state/indexes/<index-id>/retrieval-profile.yaml` — how to chunk and retrieve them

**Source inventory decisions:**
1. Which directories or files are in scope?
2. What priority does each source have? (high = block if unavailable; low = skip gracefully)
3. Are any transforms needed? (OpenAPI → Markdown, PDF → text)
4. What tags should be assigned per source? (used for retrieval filtering)

**Retrieval profile decisions:**
1. Chunking strategy per document type (markdown: split at ##; code: function boundaries)
2. Max chunk size (default: 500 tokens)
3. Overlap between chunks (default: 50 tokens; increase for runbooks/procedures)
4. Metadata fields to extract
5. Minimum retrieval score (default: 0.5; raise to 0.7 for precision-critical tasks)
6. Benchmark queries for validation (5 minimum)

**See:** `examples/knowledge-system/retrieval-profile.yaml` for a complete example.

---

## Step 2: Scaffold the Index Directory

```bash
./scripts/build_document_index.sh --index-id <your-index-id>
```

This creates:
```
state/indexes/<index-id>/
  manifest.yaml          ← status: building
  source-inventory.yaml  ← stub (fill in from Step 1)
  retrieval-profile.yaml ← stub (fill in from Step 1)
  build-log.md           ← empty log
  chunks/                ← will be populated by knowledge-curator
  metadata/
```

If the retrieval-architect already produced the inventory and profile, copy them in:

```bash
cp examples/knowledge-system/source-inventory.yaml state/indexes/<index-id>/source-inventory.yaml
cp examples/knowledge-system/retrieval-profile.yaml state/indexes/<index-id>/retrieval-profile.yaml
```

---

## Step 3: Build the Index

Run the swarm cycle — the knowledge-curator agent picks up the `index-build-prompt.md` that the scaffold script generated:

```bash
./scripts/run_swarm_cycle.sh
```

The knowledge-curator will:
1. Read `source-inventory.yaml` and `retrieval-profile.yaml`
2. Execute the `document-indexing` skill
3. Chunk all accessible sources
4. Write chunks to `state/indexes/<index-id>/chunks/`
5. Write per-source results to `build-log.md`
6. Update `manifest.yaml` when done

**Monitor progress:**

```bash
# Check build log (tailing the per-source results)
cat state/indexes/<index-id>/build-log.md

# Check manifest status
grep "^status:" state/indexes/<index-id>/manifest.yaml
```

---

## Step 4: Validate Index Quality

The evaluator runs benchmark queries against the completed index:

**Automatic validation (in swarm cycle):**
- The knowledge-curator runs a test retrieval after building
- Benchmark queries are defined in `retrieval-profile.yaml`
- Pass threshold: score ≥ 0.6 (configurable)

**Manual validation:**

```bash
# Inspect chunk count
ls state/indexes/<index-id>/chunks/ | wc -l

# Check skip rate
grep "skipped_sources:" state/indexes/<index-id>/manifest.yaml
grep "total_sources:" state/indexes/<index-id>/manifest.yaml
```

**Quality thresholds:**
- < 10% sources skipped: OK
- 10–30% skipped: warn (log in build-log.md, continue)
- > 30% skipped: escalate before finishing build

---

## Step 5: Retrieval in Agent Tasks

Once the index is built, agents use the `long-document-retrieval` skill to query it:

```yaml
# In a task brief:
skill: long-document-retrieval
index_id: <your-index-id>
query: "What is the failover procedure for the primary database?"
top_k: 5
min_score: 0.65
filter:
  doc_type: runbook
```

The skill returns ranked chunks. Agents use these chunks as context instead of reading raw documents.

**When to use retrieval vs. direct read:**
- > 5 documents: use retrieval
- ≤ 5 documents: read directly (more accurate, no index needed)
- Known document + known section: read directly (more precise)
- Unknown which document: use retrieval

---

## Step 6: Maintaining the Index

### Incremental Rebuild (New/Changed Documents)

```bash
./scripts/build_document_index.sh --index-id <id> --rebuild
```

Use when:
- New documents added to an indexed source directory
- Existing documents changed materially (> 20% content change)

### Full Rebuild (Profile Change)

Requires human approval (per AGENTS.md). After approval:

```bash
./scripts/build_document_index.sh --index-id <new-id>
# Use a new index ID for full rebuilds to preserve the old index
```

Reason: full rebuilds can take significant time and storage. Require deliberate operator decision.

### Staleness Warning

The retrieval profile sets `max_staleness_days`. If the index is older than this threshold:
- The knowledge-curator logs a staleness warning
- The orchestrator includes it in the next cycle report
- Human operator decides whether to rebuild

---

## Step 7: Archiving Old Indexes

Indexes older than 90 days are archived by the knowledge-curator:

```bash
# Manual archive if needed
mv state/indexes/<old-id>/ state/artifacts/indexes/<old-id>/
```

The `state/artifacts/` directory is gitignored — archived indexes are not committed.

---

## Common Problems

### High Skip Rate (> 30%)

**Diagnosis:**
1. Check `build-log.md` for which sources were skipped and why
2. Common reasons: path doesn't exist, access permissions, format not supported

**Resolution:**
1. Fix path issues in `source-inventory.yaml`
2. Pre-convert unsupported formats (PDF → text)
3. For credential-gated sources: request human approval to provide credentials
4. If the high-priority sources are all inaccessible: escalate before continuing

### Low Retrieval Score (< 0.5)

**Diagnosis:**
1. Check if benchmark queries match the language used in source documents
2. Check chunk size — very large or very small chunks reduce retrieval quality
3. Check if the wrong sections are being split (e.g., splitting mid-sentence)

**Resolution:**
1. Adjust `split_at` and `max_tokens` in `retrieval-profile.yaml`
2. Run retrieval-architect to redesign the chunking strategy
3. Rebuild index with new profile

### Index Build Is Slow

- Log progress to `build-log.md` — the knowledge-curator should update it per source
- Do not abort unless orchestrator explicitly requests it (per AGENTS.md failure modes)
- After build: report duration in build-log.md and flag if > expected time

### Agents Querying Before Index Is Ready

Check `manifest.yaml` before using retrieval:

```bash
grep "^status:" state/indexes/<id>/manifest.yaml
# Must be "complete" before agents use the index
```

If status is `building` or `partial`, wait for the knowledge-curator to finish.

---

## Related Documents

- `docs/knowledge-retrieval.md` — architecture and index lifecycle
- `skills/document-indexing/SKILL.md` — indexing skill interface
- `skills/long-document-retrieval/SKILL.md` — retrieval skill interface
- `agents/retrieval-architect.md` — index design decisions
- `agents/knowledge-curator.md` — index build and maintenance
- `examples/knowledge-system/` — complete worked example
