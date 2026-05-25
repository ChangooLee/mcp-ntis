# Quality Gates

This document defines all quality gates used in the master swarm project, organized by project type.

---

## Universal Gates (All Project Types)

Every project must pass these three gates before completion.

### Gate: Completeness

**ID:** `universal-completeness`  
**Description:** All required deliverables are present and located in the expected locations.  
**Owner:** evaluator  
**Pass criteria:**
- All tasks in the task graph are DONE or explicitly scoped out
- All deliverable files exist
- All deliverables are non-empty
**Fail criteria:**
- Any task is PENDING or ACTIVE when release-packaging starts
- Any required file is missing
**Evidence required:** Task graph status report  
**Retry budget:** 2

---

### Gate: Correctness

**ID:** `universal-correctness`  
**Description:** Outputs meet the stated acceptance criteria from task briefs.  
**Owner:** evaluator  
**Pass criteria:**
- Each task's acceptance criteria have been verified (per validation.md)
- No known regressions
**Fail criteria:**
- Any acceptance criterion is unmet
- Any known regression
**Evidence required:** task validation.md for each task  
**Retry budget:** 2

---

### Gate: Handoff Quality

**ID:** `universal-handoff`  
**Description:** The operator can take over the project without additional questions to the swarm.  
**Owner:** release-manager  
**Pass criteria:**
- Final run summary is complete and specific
- All required next steps are documented
- All pending approvals are explicitly listed
**Fail criteria:**
- Summary is vague or missing
- Next steps are unclear
**Evidence required:** state/runs/<run-id>/summary.md  
**Retry budget:** 1

---

## Software Project Gates

Apply when `project_type` is `backend-service`, `frontend-web`, or `full-stack`.

### Gate: Test Coverage

**ID:** `sw-test-coverage`  
**Description:** New code has associated tests.  
**Owner:** tester  
**Pass criteria:**
- All new public functions have at least one unit test
- All new error paths have a negative test
- No existing tests are broken
**Evidence required:** Test run output  
**Retry budget:** 2

---

### Gate: No Regressions

**ID:** `sw-no-regressions`  
**Description:** Existing test suite continues to pass.  
**Owner:** tester  
**Pass criteria:** All tests that passed before this run still pass  
**Fail criteria:** Any previously passing test now fails  
**Evidence required:** Before/after test run comparison  
**Retry budget:** 3

---

### Gate: API Documentation

**ID:** `sw-api-docs`  
**Description:** All new or changed API endpoints are documented.  
**Owner:** documenter  
**Pass criteria:**
- OpenAPI spec or equivalent covers all endpoints
- Breaking changes are called out explicitly
**Evidence required:** API doc file or diff  
**Retry budget:** 1

---

## Research Project Gates

Apply when `project_type` is `research-report`.

### Gate: Citations Present

**ID:** `research-citations`  
**Description:** All factual claims in the synthesis are backed by a logged source.  
**Owner:** researcher  
**Pass criteria:** Every claim in synthesis.md has a reference to evidence-log.md  
**Fail criteria:** Any unsupported factual claim  
**Evidence required:** synthesis.md + evidence-log.md  
**Retry budget:** 2

---

### Gate: Contradictions Addressed

**ID:** `research-contradictions`  
**Description:** All contradictions between sources are explicitly surfaced.  
**Owner:** researcher  
**Pass criteria:** synthesis.md has a contradictions section (empty is acceptable if no contradictions found)  
**Evidence required:** synthesis.md  
**Retry budget:** 1

---

### Gate: Synthesis Complete

**ID:** `research-synthesis`  
**Description:** The research question is directly answered with stated confidence.  
**Owner:** researcher + evaluator  
**Pass criteria:**
- Research question is restated and answered
- Confidence level is stated and justified
- Limitations are documented
**Evidence required:** synthesis.md  
**Retry budget:** 2

---

## Data/ETL Project Gates

Apply when `project_type` is `data-etl`.

### Gate: Schema Valid

**ID:** `data-schema-valid`  
**Description:** All schemas are valid and consistent with documentation.  
**Owner:** tester  
**Pass criteria:** Schema validation passes with zero errors  
**Evidence required:** Validation tool output  
**Retry budget:** 3

---

### Gate: Data Quality Metrics

**ID:** `data-quality`  
**Description:** Data quality metrics meet defined thresholds.  
**Owner:** evaluator  
**Pass criteria:** All defined metrics (completeness, uniqueness, validity) meet thresholds  
**Evidence required:** Data quality report  
**Retry budget:** 2

---

### Gate: Reproducible Pipeline

**ID:** `data-reproducible`  
**Description:** The pipeline can be re-run from scratch and produce the same result.  
**Owner:** tester  
**Pass criteria:** Fresh run produces same output (within tolerance)  
**Evidence required:** Two run outputs comparison  
**Retry budget:** 2

---

## Documentation Project Gates

Apply when `project_type` is `internal-docs`.

### Gate: Internal Links Valid

**ID:** `docs-links-valid`  
**Description:** All internal links within documentation are valid (not 404).  
**Owner:** documenter  
**Evidence required:** Link check report  
**Retry budget:** 2

---

### Gate: Accuracy Review Complete

**ID:** `docs-accuracy`  
**Description:** Documentation has been reviewed for accuracy against the system it describes.  
**Owner:** reviewer  
**Pass criteria:** Review complete; all inaccuracies resolved  
**Evidence required:** Review report or sign-off  
**Retry budget:** 1

---

## Automation/Workflow Project Gates

Apply when `project_type` is `automation-workflow`.

### Gate: Integration Tested

**ID:** `auto-integration-tested`  
**Description:** Automation has been tested end-to-end with realistic inputs.  
**Owner:** tester  
**Evidence required:** Integration test run output  
**Retry budget:** 2

---

### Gate: Idempotent

**ID:** `auto-idempotent`  
**Description:** Running the automation twice produces the same result (no side-effect accumulation).  
**Owner:** tester  
**Evidence required:** Two-run comparison  
**Retry budget:** 2

---

### Gate: Rollback Documented

**ID:** `auto-rollback`  
**Description:** Rollback procedure is documented for all destructive or state-changing operations.  
**Owner:** documenter  
**Evidence required:** Rollback section in runbook  
**Retry budget:** 1

---

## Running Quality Gates

```bash
# Run all gates for the current project
bash scripts/run_quality_gates.sh

# Check which gates are required for a project type
cat docs/project-types.md | grep -A 20 "<type>"
```

---

## Related Documents

- `scripts/run_quality_gates.sh` — gate runner
- `templates/QUALITY_GATES.template.md` — per-project gate configuration
- `docs/project-types.md` — project type gate assignments
- `AGENTS.md §9` — validation protocol
