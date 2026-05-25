# License Documentation

This document records the licenses of all upstream repositories integrated into the master swarm project.

---

## This Project

**License:** MIT  
**Copyright:** 2026 Master Swarm Project Contributors  
**File:** LICENSE

---

## Upstream Licenses

| Upstream | Known License | Notes |
|---|---|---|
| agentsmd/agents.md | MIT | Conceptual reference only |
| anthropics/skills | MIT / Apache-2.0 | Check individual files in external/upstreams/skills/LICENSE |
| revfactory/harness | Unknown | Verify before any code vendoring |
| bytedance/deer-flow | Apache-2.0 | Conceptual reference only |
| aiming-lab/AutoResearchClaw | Unknown | Verify before any code vendoring |
| supermemoryai/supermemory | Apache-2.0 | Conceptual reference only |
| karpathy/autoresearch | MIT | Conceptual reference only |
| VoltAgent/awesome-claude-code-subagents | Unknown | Verify before any code vendoring |
| obra/superpowers | Unknown | Verify before any code vendoring |
| dwzhu-pku/PaperBanana | Unknown | Verify before any code vendoring |
| msitarzewski/agency-agents | Unknown | Verify before any code vendoring |
| HKUDS/ClawTeam | Unknown | Verify before any code vendoring |

---

## License Verification Process

After cloning upstreams via `scripts/clone_upstreams.sh`, verify licenses:

```bash
# Check license files for all cloned upstreams
for dir in external/upstreams/*/; do
  echo "=== $(basename $dir) ==="
  cat "$dir/LICENSE" 2>/dev/null || cat "$dir/LICENSE.md" 2>/dev/null || echo "No license file found"
  echo ""
done
```

---

## Vendoring Policy

**We do not vendor upstream code** in the master project.

All upstream content is:
- Referenced conceptually (ideas, patterns, approaches)
- Attributed in `docs/upstreams.md` and `upstreams/manifest.yaml`
- Cloned locally to `external/upstreams/` (gitignored) for reference

If any upstream code is ever vendored (e.g., a specific utility function):
1. Verify the license permits vendoring
2. Copy the relevant license to `upstreams/adapters/<name>/LICENSE`
3. Add the file to `upstreams/manifest.yaml` with `integration_mode: vendored`
4. Add attribution comments to the vendored file
5. Update this document

---

## Apache 2.0 Projects

For upstreams under Apache 2.0 (deer-flow, supermemory):
- Conceptual reference: no notice required
- If code is adapted: include the Apache 2.0 NOTICE in the adapted file

---

## Unknown License Projects

For upstreams without a confirmed license (marked "Unknown" above):
- Do not vendor any code
- Conceptual reference only
- Verify license before using in any commercial context

---

## Updates

After running `scripts/clone_upstreams.sh`, run the license verification above and update the table with confirmed licenses.
