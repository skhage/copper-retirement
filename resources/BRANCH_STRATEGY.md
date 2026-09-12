# Branch Strategy — Copper Retirement Multi-Agent Repo

**Author:** @devops | **Date:** 2026-09-12 | **Status:** Active

---

## 1. Constraints

- **Single Git folder.** All agents share one Databricks workspace Git folder
  (`/Users/stephen.hage@databricks.com/copper-retirement`). Only one branch can
  be checked out at a time.
- **Non-CLI Git folder.** Git operations use the `runGit` API (Projects/Repos).
  `merge`, `rebase`, `stash`, `log`, and `blame` are **not available** via API.
  Only `status`, `checkout`, `commit_and_push`, `pull`, `diff`,
  `discard_changes`, and `list_branches` are supported.
- **Sequential agent execution.** Agents run via scheduled tasks on non-overlapping
  cadences. No two agents execute simultaneously in the same Git folder.
- **DML approved.** CEO directive (2026-09-11): agents may execute DML without
  human approval during scheduled runs.

---

## 2. Branching Model: Trunk-Based Development

Given the single-workspace constraint and sequential execution, we use
**trunk-based development on `main`** with short-lived topic branches for
multi-session work.

### 2.1 `main` — Integration Branch

- **All routine agent work commits directly to `main`.** This includes data gen
  outputs, config updates, spec files, notebook edits, and small fixes.
- Every agent run starts with `pull` to sync, then commits at the end.
- Commit messages follow the convention in Section 4.

### 2.2 Topic Branches — For Multi-Session or Risky Work

Create a topic branch when:
- The work spans **multiple agent runs** and intermediate states would break
  other agents (e.g., a half-migrated schema, an incomplete pipeline refactor).
- The work is **experimental** and may be reverted (e.g., ML model architecture
  experiments, app UI overhauls).
- The work requires **human review** before merging (e.g., DAB config changes
  that affect production deployment).

**Naming convention:** `<role>/<task-code-or-description>`

| Agent Role       | Branch Prefix     | Example                                |
|------------------|-------------------|----------------------------------------|
| @data-engineer   | `data-eng/`       | `data-eng/DATAGEN-CFS`                 |
| @data-analyst    | `analyst/`        | `analyst/gap-analysis-v2`              |
| @data-planner    | `planner/`        | `planner/domain-rescan`                |
| @ml-engineer     | `ml/`             | `ml/P4-RISK-classifier`               |
| @app-developer   | `app/`            | `app/copper-map-v2`                    |
| @pm              | `pm/`             | `pm/build-plan-restructure`            |
| @qa              | `qa/`             | `qa/test-coverage-sweep`               |
| @devops          | `devops/`         | `devops/dab-staging-target`            |
| @designer        | `designer/`       | `designer/brand-review-fixes`          |
| Human/CEO        | `feature/`        | `feature/lakebase-task-board`          |

### 2.3 Branch Lifecycle

1. **Create:** Agent checks out a new branch before starting multi-session work.
2. **Work:** Agent commits to the topic branch across runs.
3. **Merge:** Human (CEO) merges via the Repos UI or GitHub PR. Agents cannot
   initiate merges via `runGit`.
4. **Delete:** @devops cleans up merged branches during REPO-HEALTH sweeps
   (see Section 6).

**Maximum branch age:** 7 days. If a topic branch is older than 7 days without
activity, @devops will flag it for cleanup or escalate to @pm.

---

## 3. Agent Run Protocol (Git Operations)

Every agent run that modifies files MUST follow this sequence:

```
1. runGit(status)          — Check current branch and dirty state
2. runGit(pull)            — Sync with remote (resolve conflicts if any)
3. [Do work]              — Create/edit files, run notebooks, etc.
4. runGit(status)          — Verify changed files before commit
5. runGit(diff)            — Review changes (sanity check)
6. runGit(commit_and_push) — Commit with descriptive message
```

**If pull produces conflicts:**
- Use `conflict_info` to inspect each conflicted file.
- Prefer `accept_file` with strategy `theirs` for files the agent did not
  modify (accept the remote version).
- For files the agent DID modify, write a hand-merged resolution and use
  `accept_file` with strategy `current`.
- Call `continue` to finalize the merge.
- If unable to resolve, call `abort` and log the conflict in Lakebase with
  status `blocked` for @devops to handle.

**If the workspace is on a topic branch and the agent's task is on `main`:**
- Do NOT switch branches if there are uncommitted changes.
- First commit or discard changes on the current branch, then checkout `main`.

---

## 4. Commit Message Convention

Format: `[@role] TASK-CODE: Short description`

Examples:
```
[@data-engineer] DATAGEN-CFS: Generate 100K customer_facing_service rows with H3
[@ml-engineer] P4-RISK: Add GBT risk classifier training notebook
[@devops] DEVOPS-BRANCH-STRATEGY: Add branch strategy document
[@app-developer] APP-MAP-SCAFFOLD: Scaffold copper-map React app
[@qa] QA-REVIEW-DATAGEN: Fix synthetic_sources.py FK constraint violations
[@pm] PM-BUILD-PLAN: Update BUILD-PLAN.md phase 2 status
```

Rules:
- **Always prefix with `[@role]`** so `git log` shows which agent authored each
  commit.
- **Include the task code** from Lakebase (`agent_tasks.task_code`) when
  applicable.
- **Keep the description under 72 characters.**
- **No WIP commits on `main`.** If work is incomplete, use a topic branch.

---

## 5. Directory Ownership (Conflict Prevention)

To minimize merge conflicts, each agent role has primary ownership of specific
directories. Agents SHOULD avoid editing files outside their owned directories
without coordinating via Lakebase task assignment.

| Directory            | Primary Owner(s)              | Secondary (with coordination) |
|----------------------|-------------------------------|-------------------------------|
| `data_gen/`          | @data-engineer                | @data-planner, @qa            |
| `data_gen/SPEC_*.md` | @data-planner, @pm            | @data-engineer                |
| `risk/`              | @ml-engineer                  | @qa                           |
| `apps/`              | @app-developer                | @designer                     |
| `bundle/`            | @devops                       | @pm                           |
| `scripts/`           | @data-engineer, @devops       | @qa                           |
| `tests/`             | @qa                           | All (add tests for own code)  |
| `resources/`         | @pm, @devops                  | @designer (brand guide)       |
| `databricks.yml`     | @devops                       | @pm (variable changes)        |
| `BUILD-PLAN.md`      | @pm                           | @data-planner                 |
| `README.md`          | @pm, @devops                  | —                             |

---

## 6. Repo Health Checks (@devops Periodic Tasks)

@devops runs periodic REPO-HEALTH sweeps to maintain hygiene:

1. **Stale branch detection:** List branches, flag any >7 days since last
   commit. Escalate to @pm for cleanup decision.
2. **Uncommitted changes audit:** Run `status` on `main`. If dirty, identify
   the owning agent and either commit or discard.
3. **Conflict marker scan:** Search for `<<<<<<<`, `=======`, `>>>>>>>` in
   tracked files. If found, the merge was incomplete — escalate immediately.
4. **DAB config validation:** Verify `databricks.yml` and
   `bundle/resources/*.yml` are syntactically valid and reference existing
   schemas/tables.
5. **Branch count cap:** If total branches exceed 10, prioritize cleanup of
   merged or abandoned branches.

---

## 7. Existing Branches (as of 2026-09-12)

| Branch | Status | Action |
|--------|--------|--------|
| `main` | Active integration branch | Keep |
| `copper-task-board-slack-ui` | Feature work — Slack UI for task board | Review for merge or archive |
| `polly/p0-thin-slice` | P0 thin-slice scaffolding (legacy) | Review — likely mergeable or stale |
| `polly/p0-uc` | UC setup (legacy) | Review — likely mergeable or stale |
| `polly/production-hardening` | Production hardening work | Review for merge |
| `polly/synthetic-data-foundation-codex-v2` | Synthetic data gen v2 | Review for merge |
| `research-files` | Research reference materials | Archive candidate |

**Action items:**
- CEO/human to review `polly/*` branches for merge readiness.
- `copper-task-board-slack-ui` and `research-files` are archive candidates if
  their content has been incorporated into `main`.
- @devops will diff each branch against `main` in a follow-up REPO-HEALTH task
  to determine divergence.

---

## 8. Emergency Procedures

**Broken `main` (tests fail, notebooks error):**
1. @devops identifies the breaking commit via `list_branches` + diff.
2. @devops creates a `hotfix/<description>` branch with the fix.
3. CEO merges the hotfix immediately.
4. @devops notifies @pm in Lakebase status notes.

**Unresolvable merge conflict:**
1. Agent calls `abort` to cancel the conflicted pull/merge.
2. Agent logs the conflict in Lakebase (`status = 'blocked'`, notes include
   the conflicted files).
3. @devops picks up the conflict resolution as a priority task.
4. If @devops cannot resolve via API, escalate to CEO for manual resolution
   in the Repos UI.

---

## 9. Future Improvements

When the project matures:
- **Add a `staging` target** in `databricks.yml` for pre-production validation.
- **Implement branch protection** on `main` if GitHub branch rules are available.
- **Add CI checks** via DAB `bundle validate` in a GitHub Action on PRs.
- **Per-agent Git folders** if concurrent execution becomes necessary (each
  agent gets its own clone of the repo).
