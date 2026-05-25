# Integration Strategy

This document describes the strategy for integrating this master project with external tools, IDEs, and agent platforms.

---

## Cursor IDE Integration

**Primary integration.** Rules in `.cursor/rules/` are loaded automatically by Cursor and applied to all agent interactions within the project.

**Setup:**
1. Open the master project (or a project based on it) in Cursor
2. Rules in `.cursor/rules/*.mdc` are automatically applied
3. AGENTS.md is read by agents on first task in the project

**What Cursor rules do:**
- Enforce the core operating model
- Remind agents to read AGENTS.md before acting
- Set boundaries for planning, routing, memory, and safety
- Route by project type

**What Cursor rules do NOT do:**
- Execute the swarm loop (that's `scripts/run_swarm_cycle.sh`)
- Store state (that's `state/`)
- Define agent roles (that's `agents/`)

---

## Claude Code CLI Integration

The project is designed to work with the Claude Code CLI (`claude` command):

```bash
# Start a swarm cycle using Claude Code
bash scripts/run_swarm_cycle.sh
# The script generates a cycle prompt in state/runs/<run-id>/cycle-prompt.md

# Execute the prompt
claude < state/runs/<run-id>/cycle-prompt.md

# Or in interactive mode
claude
# Then: read README.md and AGENTS.md and run the swarm
```

**Claude-specific features used:**
- Reading multiple files (README, AGENTS, recon, state)
- Writing files (task outputs, logs, manifests)
- Tool use for file operations

---

## GitHub Actions Integration

For automated swarm runs in CI:

```yaml
# .github/workflows/swarm-run.yml
name: Swarm Run
on: [push, workflow_dispatch]
jobs:
  swarm:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Bootstrap
        run: bash scripts/bootstrap.sh
      - name: Scaffold cycle
        run: bash scripts/run_swarm_cycle.sh
      - name: Execute cycle (requires ANTHROPIC_API_KEY)
        run: claude < state/runs/*/cycle-prompt.md
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Note:** Actual CI integration requires an Anthropic API key and the Claude CLI installed in the runner.

---

## VS Code Integration

`.cursor/rules/` rules work as standard Cursor rules. For VS Code without Cursor, agents can read `AGENTS.md` directly without rule enforcement.

---

## Multi-Agent Platform Integration

For platforms that support multiple parallel agents:

1. Spawn the orchestrator agent with the cycle prompt
2. The orchestrator dispatches tasks to specialist agents (via the platform's messaging)
3. Each specialist agent reads its task brief from `state/tasks/<id>/brief.md`
4. Outputs are written to `state/tasks/<id>/outputs/`
5. The orchestrator reads outputs and updates the manifest

This architecture is platform-agnostic — any platform that can read/write files can host the swarm.

---

## Memory System Integration Options

Current: flat markdown files in `state/memory/`

**Alternative integrations:**
- **Supermemory:** Replace `state/memory/` with Supermemory API calls (update memory-update skill)
- **Vector DB:** Add embedding-based retrieval for pattern memory (update repo-recon skill)
- **Git-based memory:** Use git history as memory (use `git log` in memory-update skill)

None of these require changes to AGENTS.md or the swarm loop — only the memory-update and repo-recon skills would change.

---

## Adding a New Integration

1. Identify the integration point (IDE, CI, memory, etc.)
2. Determine which skill or script handles that integration point
3. Create or update the relevant skill/script
4. Test the integration on an example project
5. Document in this file and in `docs/decisions/`
6. Do not modify AGENTS.md or core rules for integration — use skill updates
