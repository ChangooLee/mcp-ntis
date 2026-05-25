# Runbook: Human Approval Process

This runbook describes how the swarm requests and receives human approval for actions that cannot be self-approved.

---

## When the Swarm Requests Approval

The swarm stops and writes an approval request when it needs to:
- Deploy or release an artifact
- Publish or send external communications
- Delete files not created in this run
- Modify CI/CD pipelines or infrastructure
- Apply self-improvement to core contracts
- Perform any action explicitly flagged `requires_approval: true`

---

## Where to Find Approval Requests

```bash
# Check for pending approvals in the latest run
cat state/runs/*/approvals-pending.md | head -50

# Or for a specific run
cat state/runs/<run-id>/approvals-pending.md
```

---

## Approval Request Format

The swarm writes requests in this format:
```markdown
# Approval Pending
Run ID: <run-id>
Date: <date>
Status: PENDING

## Action Requested
<What the swarm wants to do>

## Why It's Needed
<Why this action is required for project completion>

## What Happens If Not Approved
<What the swarm will do instead — typically mark the task blocked>

## Alternatives Considered
<Any alternatives the swarm evaluated>

## How to Approve
Add `approved: true` below and re-run the swarm cycle.

approved: false
approved_by:
approval_date:
approval_notes:
```

---

## How to Approve

1. Read the approval request carefully
2. Evaluate: is this action appropriate given the project goals?
3. If approving:
   ```bash
   # Edit the file
   nano state/runs/<run-id>/approvals-pending.md
   # Set: approved: true
   # Set: approved_by: <your-name>
   # Set: approval_date: <today>
   
   # Then resume the swarm
   bash scripts/run_swarm_cycle.sh
   ```

4. If rejecting:
   ```bash
   # Edit the file
   nano state/runs/<run-id>/approvals-pending.md
   # Set: approved: false
   # Set: approval_notes: <reason for rejection, alternatives>
   
   # Add constraints to AGENTS.md or README.md
   # Then resume — swarm will work around the rejected action
   bash scripts/run_swarm_cycle.sh
   ```

---

## What Happens After Approval

- The swarm reads the approval on the next cycle
- If approved: proceeds with the action
- If rejected: marks the task BLOCKED and continues with remaining tasks
- If partially approved (some items yes, some no): the swarm handles each independently

---

## Common Approval Scenarios

### Scenario: Deploy to staging

**Request:** "Deploy the built artifact to staging environment"
**Evaluate:** Is staging deployment safe at this point? All tests passing?
**Approve if:** Tests pass, artifact is complete
**Reject if:** Any quality gate is failing

### Scenario: Delete legacy files

**Request:** "Delete src/legacy/ — confirmed unused after recon"
**Evaluate:** Is this safe? Are we sure nothing depends on it?
**Approve if:** You have verified nothing references these files
**Reject if:** Uncertain — mark for manual review

### Scenario: Apply self-improvement to AGENTS.md

**Request:** "Modify AGENTS.md §16 to change retry budget from 3 to 5"
**Evaluate:** Is this improvement evidence-based? What failure prompted it?
**Approve if:** You've read the retrospective and agree with the reasoning
**Reject if:** Change seems overly broad or unsupported

---

## Escalation

If you receive a confusing or concerning approval request:
1. Do not approve it
2. Add a note: `approval_notes: Confused by this request. Needs investigation.`
3. Check `state/runs/<run-id>/cycle-log.md` to understand what led to this request
4. Check `state/reflections/` for relevant context
5. Start a new run with clarified AGENTS.md if needed
