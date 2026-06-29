---
name: github-async-handoff
version: 1.0.0
description: >
  Decentralized async task handoff for multi-agent clusters using GitHub as a 
  serverless task queue. Agents create/claim/complete Issues as "work tickets", 
  push/pull artifacts via Git branches -- no real-time connectivity required.
  Ideal for cross-timezone collaboration, CI/CD pipeline handoffs, and any 
  scenario where agents operate on different schedules.
author: open-source-contributors
license: MIT
tags: [multi-agent, async-handoff, github-issues, task-queue, decentralized]
---

# github-async-handoff

## Concept: GitHub as a Decentralized Task Queue

Traditional agent coordination demands synchronized runtimes: message brokers, shared databases, or real-time messaging layers. **github-async-handoff** proposes a different model -- **GitHub Issues become work tickets, Git branches become artifact channels, and the entire coordination protocol requires zeroinfrastructure beyond a GitHub repository.**

Core innovation:

- **Issue = Task Ticket**: Create → Claim → Complete → Close, full lifecycle with timestamps and audit trail
- **Branch = Artifact Channel**: Each agent pushes to `handoff/{agent_id}`, a designated merger agent consolidates to main
- **Rate-limit-aware**: Local cache for intermediate states, API calls only on state transitions (create/claim/close = 3 calls per task)
- **Zero deploy**: No Redis, no RabbitMQ, no database -- just a GitHub repo and a Personal Access Token

### When to Use

| Situation | Recommended Layer |
|-----------|-------------------|
| Agents on the same network, need real-time sync | Direct P2P or real-time messaging layer |
| Agents on different schedules, need async handoff | **github-async-handoff** |
| Human-in-the-loop oversight needed | Group chat / messaging platform |
| Sensitive data transmission | Encrypted channel only |

### Comparison with Alternatives

| Dimension | github-async-handoff | RabbitMQ | Redis Queue (RQ/Celery) | GitHub Issues (raw) |
|-----------|---------------------|----------|------------------------|---------------------|
| Deployment | Zero (just a repo) | Broker + config (~30min) | Redis instance (~5min) | Zero (just a repo) |
| Protocol | REST API + Git | AMQP | Redis protocol | REST API only |
| Artifact transfer | Git push/pull (built-in) | Not built-in | Not built-in | Manual attachment |
| Audit trail | Issue history + commit log (built-in) | Requires plugin | Requires plugin | Issue history only |
| Rate limit | 5000 req/hour (auth) | None (self-hosted) | None (self-hosted) | 5000 req/hour (auth) |
| Human visibility | Excellent (GitHub UI) | None | None | Excellent (GitHub UI) |
| Offline tolerance | Full (agents can be days apart) | Consumers must connect | Workers must connect | Full |
| Concurrent push conflict | Branch-per-agent strategy | N/A | N/A | N/A (no artifact transfer) |
| Cost | Free (public/private repo) | Server cost | Server cost | Free |

**Key differentiator**: github-async-handoff is the only solution that gives you *both* task coordination (Issues) and artifact transfer (Git) with built-in audit and zero infrastructure, making it uniquely suited for agent clusters that span timezones, organizations, or intermittent connectivity.

---

## State Machine

Every task follows this lifecycle:

```
CREATED ──→ CLAIMED ──→ COMPLETED ──→ CLOSED
   │            │            │
   │            └──→ BLOCKED ──→ CLAIMED (retry)
   │
   └──→ EXPIRED (timeout, auto-transition)
```

| State | GitHub Representation | Meaning |
|-------|----------------------|---------|
| CREATED | Open Issue, unassigned | Task posted, waiting for an agent |
| CLAIMED | Open Issue, assigned to agent | Agent picked up the task |
| COMPLETED | Open Issue with `review-pending` label | Agent finished, awaiting review/approval |
| CLOSED | Closed Issue with summary comment | Task done and verified |
| BLOCKED | Open Issue with `blocked` label | Agent hit a dependency, needs help |
| EXPIRED | Closed Issue with `expired` label | Noclaim within deadline |

---

## File Naming Convention

Handoff artifacts follow a strict naming convention to ensure discoverability:

```
{task_type}_{identifier}_{timestamp}_{sequence}
```

| Component | Description | Example |
|-----------|-------------|---------|
| task_type | Category of work | data_analysis, code_review, report_draft |
| identifier | Unique ID for the task | 20260628, project_alpha |
| timestamp | Date stamp | 20260628 |
| sequence | Sequence number (3-digit) | 001, 002, 003 |

Full example: `data_analysis_20260628_001`

Branch naming follows `handoff/{agent_id}` pattern:
- `handoff/agent-alpha`
- `handoff/agent-beta`
- `handoff/agent-gamma`

---

## Python API

```python
from github_async_handoff import HandoffClient

handoff = HandoffClient(
    repo="your-org/agent-workspace",
    token="ghp_xxxxxxxxxxxx"
)

# --- Create a handoff task ---
issue = handoff.create_handoff(
    title="[Handoff] Data analysis report draft",
    body="## Handoff Content\n"
         "- File: /output/analysis_report_v1.docx\n"
         "- Status: Draft complete, pending review\n"
         "- Deadline: 2026-07-15",
    labels=["handoff", "review-pending"],
    assignee="agent-beta"
)
print(f"Issue #{issue.number} created")

# --- Agent comes online and claims the task ---
handoff.claim_handoff(issue_number=42, assignee="agent-beta")

# --- Agent completes and closes the task ---
handoff.complete_handoff(
    issue_number=42,
    summary="Review passed, 3 wording fixes applied"
)

# --- Push artifacts to per-agent branch ---
handoff.push_code(
    branch="handoff/agent-alpha",
    files={
        "output/analysis_report_v2.docx": local_file_path,
        "output/analysis_data.json": local_json_path
    },
    commit_message="[Handoff] Analysis report v2 with review fixes"
)

# --- Pull artifacts from another agent's branch ---
artifacts = handoff.pull_code(
    branch="handoff/agent-beta",
    path="output/"
)

# --- Query pending handoffs ---
pending = handoff.list_pending(task_type="data_analysis")
for task in pending:
    print(f"#{task.number}: {task.title} [{task.state}]")

# --- Check if a specific task is ready ---
ready = handoff.is_ready(issue_number=42)

# --- Mark task as blocked ---
handoff.block_handoff(
    issue_number=42,
    reason="Waiting for upstream data from Agent Gamma"
)

# --- Expire stale tasks ---
expired_count = handoff.expire_stale(
    max_age_hours=72,
    task_type="data_analysis"
)
```

---

## Usage Scenarios

### 1. Multi-Agent Cluster Collaboration (Primary)

Agent Alpha finishes data collection at 5 PM, but Agent Beta won't come online until 9 AM tomorrow. Alpha pushes results to `handoff/agent-alpha` branch and creates an Issue: "Data collection done, Agent Beta please analyze tomorrow." Next morning, Beta pulls the latest data, claims the Issue, completes analysis, and closes with a summary.

### 2. Open-Source Collaboration

A maintainer creates an Issue describing a feature request. A contributor claims it, pushes WIP code to a branch, and links the PR to the Issue. The maintainer reviews, requests changes, and the contributor updates. The Issue closes when the PR merges.

### 3. CI/CD Pipeline Handoff

A build agent creates an Issue when a build completes, attaching artifact metadata. A test agent claims the Issue, runs test suites against the build artifacts, and reports results back. A deploy agent picks up passed tests for staging deployment.

### 4. Cross-Timezone Team Coordination

Team in UTC+8 finishes analysis and creates a handoff Issue. Team in UTC-5 starts their day, claims the Issue, continues the work, and pushes results back. The entire handoff history is traceable through Issue comments and commit timestamps.

### 5. Education / Classroom Scenario

An instructor creates Issues as assignment tickets. Students (each running their own agent) claim assignments, submit solutions via branch pushes, and the instructor reviews and closes Issues with feedback comments.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | Yes | - | Personal Access Token with `repo` scope |
| `HANDOFF_REPO` | Yes | - | Target repository in `owner/repo` format |
| `HANDOFF_BRANCH_PREFIX` | No | `handoff/` | Prefix for per-agent branches |
| `HANDOFF_DEFAULT_LABELS` | No | `handoff` | Comma-separated default labels |
| `HANDOFF_STALE_HOURS` | No | `72` | Hours before a task is considered stale |
| `HANDOFF_API_CACHE_TTL` | No | `300` | Local cache TTL in seconds |

### Label Schema

| Label | Meaning |
|-------|---------|
| `handoff` | Root label for all handoff tasks |
| `review-pending` | Artifact submitted, awaiting review |
| `blocked` | Agent hit a dependency |
| `expired` | Task exceeded deadline without being claimed |
| `data_analysis` | Task type: data analysis |
| `code_review` | Task type: code review |
| `report_draft` | Task type: report drafting |

---

## Pitfalls and Solutions

### 1. GitHub API Rate Limiting

**Problem**: Authenticated users get 5000 requests/hour. Naive implementations that call the API on every push easily exceed this under load.

**Solution**: Local cache for Issue state. Only call the API on actual state transitions (create / claim / close = 3 API calls per task). All intermediate operations read from cache.

### 2. Concurrent Push Conflicts

**Problem**: Two agents pushing to the same branch cause Git conflicts.

**Solution**: Branch-per-agent strategy. Each agent pushes to `handoff/{agent_id}` exclusively. A designated merger agent consolidates branches to main. No two agents ever push to the same branch.

### 3. Token Expiration During Failover

**Problem**: When using this skill as a failover channel (e.g., after a real-time messaging layer goes down), the GitHub token may have expired during the period of non-use.

**Solution**: Test the token on first use after failover. Implement a `validate_token()` method that calls `GET /user` before any write operation. Rotate tokens proactively before expiry.

### 4. Large Artifact Size

**Problem**: Git struggles with large binary files (models, datasets, large reports).

**Solution**: Use Git LFS for files >50MB, or store only metadata/paths in Git and transfer large artifacts through object storage with the path referenced in the Issue body.

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Agent Alpha  │     │ Agent Beta  │     │ Agent Gamma  │
│ (Producer)   │     │ (Consumer)  │     │ (Consumer)   │
└──────┬───────┘     └──────┬──────┘     └──────┬───────┘
       │                    │                    │
       │ create_handoff()   │ claim_handoff()    │ claim_handoff()
       │ push_code()        │ pull_code()        │ pull_code()
       │                    │ complete_handoff()  │ complete_handoff()
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                    GitHub Repository                     │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │  Issues   │  │ Git Branches │  │ Commit History │    │
│  │ (Tickets) │  │ (Artifacts)  │  │  (Audit Log)   │    │
│  └──────────┘  └──────────────┘  └────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**Three storage planes in one repository**:
1. **Issues** = Task coordination (who does what, when, with what status)
2. **Branches** = Artifact transfer (code, data, documents)
3. **Commit History** = Audit trail (immutable, timestamped, attributed)

---

## Integration with Other Communication Layers

github-async-handoff is one layer in a multi-tier communication architecture:

```
L5: Health Monitoring     ← cluster-health-monitor
L4: Async Handoff         ← github-async-handoff (THIS SKILL)
L3: Group Collaboration   ← messaging platform bots
L2: Message Bus           ← real-time messaging layer
L1: Direct P2P            ← direct connectivity layer
```

**L4 fallback pattern**: When L2 (message bus) goes down, github-async-handoff serves as the degraded-mode channel. Messages that would go through the message bus are instead serialized as Issue comments, ensuring no task is lost during outages.

**Transition protocol**:
1. Detect L2 failure (health monitor emits alert)
2. Switch to `HandoffClient` for all inter-agent communication
3. Serialize messages as Issue body/comments with structured JSON
4. When L2 recovers, replay unresolved Issues back to the message bus
5. Close all fallback Issues with `[FAILOVER-RESOLVED]` prefix

---

## Quick Start

```bash
# 1. Set environment variables
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export HANDOFF_REPO="your-org/agent-workspace"

# 2. In your agent code
from github_async_handoff import HandoffClient

handoff = HandoffClient(
    repo="your-org/agent-workspace",
    token="ghp_xxxxxxxxxxxx"
)

# 3. Create your first handoff
issue = handoff.create_handoff(
    title="[Handoff] First async task",
    body="Hello from Agent Alpha. Please process and close.",
    labels=["handoff"],
)
print(f"Created Issue #{issue.number}")

# 4. From another agent, claim and complete
handoff.claim_handoff(issue_number=issue.number, assignee="agent-beta")
handoff.complete_handoff(
    issue_number=issue.number,
    summary="Task processed successfully."
)
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `403 Forbidden` on Issue create | Token lacks `repo` scope | Regenerate token with full `repo` scope |
| `422 Validation Failed` on push | Branch name conflict | Ensure agent uses its own `handoff/{agent_id}` branch |
| `409 Conflict` on push | Concurrent push to same branch | Never share branches; use branch-per-agent |
| Issue created but not showing | Wrong repository path | Verify `owner/repo` format and token access |
| Rate limit hit after 1 hour | API called on every operation | Enable local cache, only call API on state transitions |
| Token expired during failover | Token not used for weeks/months | Call `validate_token()` before failover operations |
