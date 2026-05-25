---
id: adversarial-review
title: Adversarial Review
version: 1.0
purpose: Systematically attack a project output — code, research synthesis, or documentation — to surface failure modes, hidden assumptions, injection points, and unsupported claims that evaluator and reviewer passes may have missed.
when_to_use:
  - Before releasing any security-sensitive system
  - Before publishing research that will be acted upon
  - When a project type is ml-ai-system (always)
  - When explicitly requested by the orchestrator
  - When the evaluator gate is passing but confidence is low
when_not_to_use:
  - On trivial output (< 50 lines, no external effects)
  - As a substitute for the evaluator's quality gate (run both)
  - Before a first implementation pass (attack finished output, not drafts)
required_inputs:
  - The completed output to be attacked (source files, synthesis memo, or document set)
  - System description (README.md or architecture doc)
  - Quality gate results (to know what was already verified)
outputs:
  - state/tasks/<id>/red-team-report.md (findings with severity ratings)
  - Proposed adversarial test cases for critical findings
  - Updated validation status if critical findings block release
related_docs:
  - agents/red-team.md
  - docs/quality-gates.md
  - AGENTS.md §9
escalation: If a critical finding indicates a security vulnerability or a fundamental design flaw that cannot be fixed within the task budget, stop immediately and escalate to the orchestrator and operator.
---

# Skill: Adversarial Review

## Purpose

Find what the optimistic paths missed. The adversarial review assumes the output is wrong until it can prove it right.

## Adversarial Review Taxonomy

| Attack category | What to check |
|---|---|
| **Input manipulation** | What happens with malformed, empty, or adversarial inputs? |
| **Trust boundary violations** | Does the system trust user-controlled data it shouldn't? |
| **State corruption** | Can the system reach an invalid state via valid operations? |
| **Denial of service** | Can large inputs or specific patterns exhaust resources? |
| **Information leakage** | Does error output reveal internal state or credentials? |
| **Injection** | SQL, command, template, prompt injection possibilities? |
| **Unsupported claims** (research) | Are conclusions backed by evidence or assumed? |
| **Cherry-picked evidence** (research) | Are contradicting sources suppressed? |
| **Scope creep** | Has the output exceeded the stated scope in ways that introduce risk? |

## Workflow

### Step 1 — Read the target

Read the output to be attacked. For code: read the full implementation. For research: read the synthesis. For docs: read the final document. Do not skip any section.

### Step 2 — Identify attack surface

List:
- All external inputs (API params, file inputs, user data, environment variables)
- All trust decisions (what is assumed to be valid without validation?)
- All state-changing operations
- All claims that are asserted without citation (research)
- All assumptions embedded in the system design

### Step 3 — Execute attacks

For each item on the attack surface, attempt:
- Boundary values (empty, max, negative)
- Invalid types (string where int expected)
- Adversarial strings (SQL, shell metacharacters, prompt injection patterns)
- Missing dependencies (what if a required resource is absent?)
- Concurrent access (if applicable)

For research:
- Find a source that contradicts a key claim
- Identify conclusions that extrapolate beyond the evidence
- Identify where confidence is overstated

### Step 4 — Classify findings

| Severity | Criteria |
|---|---|
| **Critical** | Exploitable by an attacker or invalidates the primary conclusion |
| **High** | Likely failure under realistic conditions; must fix before release |
| **Medium** | Edge case; degrades quality but doesn't break primary function |
| **Low/Info** | Good-to-know; doesn't affect release decision |

### Step 5 — Write red-team report

`state/tasks/<id>/red-team-report.md`:
```markdown
# Red Team Report: <task-id>
Date: <date>
Target: <what was attacked>
Attack surface items identified: <n>
Findings: <n critical, n high, n medium, n low>

## Critical Findings
### Finding C1: <title>
Attack vector: <how>
Impact: <what breaks>
Evidence: <specific example or reproduction steps>
Proposed fix: <specific remediation>
Adversarial test case: <what to add to test suite>

## High Findings
...

## Release recommendation
BLOCK: critical findings present | PASS: no critical or high findings | CONDITIONAL: high findings with documented workaround
```

### Step 6 — Propose adversarial test cases

For every Critical and High finding, write a specific test case:
```
Test: <name>
Input: <specific adversarial input>
Expected behavior: <what should happen>
Observed behavior: <what actually happens>
```

## Do

- Attack with specific inputs, not vague "could be attacked" claims
- Rate severity based on realistic exploitability, not theoretical possibility
- Propose specific remediations, not "add more validation"
- Check that the fix for one finding doesn't introduce another

## Don't

- Don't duplicate evaluator gate findings — focus on what wasn't caught
- Don't rate everything Critical — this inflates severity and hides real issues
- Don't attack architectural decisions made before this run — stay in scope
- Don't release a Critical finding as "acceptable risk" — escalate instead
