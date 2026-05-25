---
id: test-authoring
title: Test Authoring
version: 1.0
purpose: Write tests that verify a feature or fix works correctly and does not regress under future changes.
when_to_use:
  - After implementing a new feature or fixing a bug
  - When a test gap is identified in an existing module
  - When a quality gate requires test coverage evidence
when_not_to_use:
  - For stub/placeholder code not yet functional
  - For documentation-only changes
  - When testing infrastructure is unavailable and cannot be set up within the task budget
required_inputs:
  - state/tasks/<id>/brief.md (what to test)
  - Source code being tested (read it first)
  - state/runs/<run-id>/recon.md (test patterns and framework)
outputs:
  - Test files following project conventions
  - state/tasks/<id>/outputs/test-report.md (summary of coverage)
related_docs:
  - docs/quality-gates.md
  - AGENTS.md §22
escalation: If the test framework is not set up and setting it up exceeds the task budget, create a task for test infrastructure setup and escalate.
---

# Skill: Test Authoring

## Purpose

Produce tests that are: specific, independent, maintainable, and aligned with the project's test patterns.

## Workflow

### Step 1 — Identify what to test

From the acceptance criteria and implementation:
- Core logic paths (happy path)
- Error paths (invalid input, network failure, etc.)
- Edge cases (empty input, max values, concurrency)
- Integration points (if integration tests are in scope)

### Step 2 — Identify test type

| Scenario | Test type |
|---|---|
| Pure function logic | Unit test |
| Module with dependencies | Unit + mocks |
| API endpoint behavior | Integration test |
| Database interactions | Integration with test DB |
| User-visible behavior | E2E (if framework exists) |

### Step 3 — Review existing tests

1. Find existing test files for the module (from recon.md)
2. Understand the existing test structure and patterns
3. Match: file naming, test organization, assertion style, mock pattern

### Step 4 — Write tests

Test structure:
```
describe('FeatureName', () => {
  describe('scenarioName', () => {
    it('should do X when Y', () => {
      // Arrange
      // Act
      // Assert
    })
  })
})
```

Each test must:
- Have a clear, specific name describing what it verifies
- Test one thing
- Be independent (not rely on order or shared state)
- Assert the outcome, not the implementation

### Step 5 — Run tests

Run the test suite and confirm:
- New tests pass
- No existing tests are broken (no regressions)

### Step 6 — Write coverage summary

`state/tasks/<id>/outputs/test-report.md`:
```markdown
# Test Report: <task-id>
Tests written: <count>
Tests passing: <count>
Coverage of new code: <estimate>
Regressions introduced: none | <list>
Known test gaps:
  -
```

## Do

- Write tests before (or alongside) code when possible
- Test behavior, not implementation details
- Use the existing test framework — don't introduce new ones without approval

## Don't

- Don't write tests that test mocks more than real behavior
- Don't skip test naming — vague test names are useless in failure reports
- Don't write tests that depend on execution order
- Don't hardcode timestamps, IDs, or environment-specific paths in tests
