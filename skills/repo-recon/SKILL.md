---
id: repo-recon
title: Repository Reconnaissance
version: 1.0
purpose: Map an existing repository's structure, conventions, tech stack, entry points, and test patterns before any modification.
when_to_use:
  - Before modifying any existing code or documents
  - When assigned to a project mid-run without prior context
  - When a new team member (agent) joins a run
when_not_to_use:
  - On a brand-new empty repository (nothing to recon)
  - When recon has already been completed this run (check state/runs/<id>/recon.md)
required_inputs:
  - Repository root directory access
outputs:
  - state/runs/<run-id>/recon.md (structured recon report)
related_docs:
  - docs/architecture.md
  - AGENTS.md §4
escalation: If the repository structure is fundamentally unclear after recon, escalate to the architect agent before making any changes.
---

# Skill: Repository Reconnaissance

## Purpose

Produce a recon report that prevents the swarm from making wrong assumptions about project structure, conventions, and existing patterns.

## Workflow

### Step 1 — Map directory structure

List top-level directories and note their apparent purpose:
```
src/           → application source
tests/         → test suite
docs/          → documentation
scripts/       → utility scripts
config/        → configuration
```

Recurse into src/ or equivalent to identify main modules/packages.

### Step 2 — Identify tech stack

Check for:
- `package.json` → Node.js / TypeScript / JavaScript
- `requirements.txt`, `pyproject.toml`, `setup.py` → Python
- `Cargo.toml` → Rust
- `go.mod` → Go
- `pom.xml`, `build.gradle` → Java/JVM
- `Dockerfile`, `docker-compose.yml` → containerized
- Framework files (next.config.js, django settings, etc.)

### Step 3 — Find entry points

- Main application file (main.py, index.ts, main.go, etc.)
- CLI entry points
- API route definitions
- Worker/job entry points

### Step 4 — Identify test patterns

- Test framework in use (pytest, jest, go test, etc.)
- Test file location convention (tests/, __tests__/, *.test.ts, etc.)
- Mock strategy (in-process mocks, fixtures, test containers)
- CI test command (from Makefile, scripts, CI config)

### Step 5 — Identify conventions

- File naming convention (camelCase, snake_case, kebab-case)
- Module/package structure
- Import style
- Config management approach
- Branch naming (from git log or .gitconfig)

### Step 6 — Write recon report

```markdown
# Recon Report: <run-id>
Date: <date>
Tech stack: <list>
Entry points:
  - <file>: <purpose>
Test framework: <name>
Test location: <pattern>
Key modules:
  - <name>: <purpose>
Conventions:
  - Naming: <style>
  - Imports: <style>
Unknown / unclear areas:
  - <description>
```

## Examples

**Good recon output:**
```
Tech stack: Node.js 20, TypeScript 5, Express 4
Entry points: src/index.ts (HTTP server), src/worker.ts (job processor)
Test framework: Jest with ts-jest
Tests: src/**/*.test.ts
Key modules: src/auth/ (JWT), src/routes/ (Express), src/db/ (Prisma)
Conventions: camelCase files, barrel exports via index.ts
Unclear: src/legacy/ — unclear if actively used
```

## Do

- Actually read package files, not just guess from directory names
- Note areas that are unclear for the architect to resolve
- Record the exact commands for running tests

## Don't

- Don't assume standard conventions without checking
- Don't skip this step when joining an existing project
- Don't report recon as "done" if you couldn't access key directories
