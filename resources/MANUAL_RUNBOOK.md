# Manual Runbook — Copper Retirement Deployment & Operations

**Author:** @devops | **Date:** 2026-09-12 | **Status:** Active

This runbook documents all steps that require human intervention, specific
ordering, or manual execution. Agents should reference this before attempting
operations that may fail without the prerequisite steps.

---

## Table of Contents

1. [Fresh Workspace Stand-Up](#1-fresh-workspace-stand-up)
2. [DAB Deployment](#2-dab-deployment)
3. [Data Generation Execution Order](#3-data-generation-execution-order)
4. [Lakebase Task Board Setup](#4-lakebase-task-board-setup)
5. [App Deployment](#5-app-deployment)
6. [ML Model Registration & Serving](#6-ml-model-registration--serving)
7. [Scheduled Task Configuration](#7-scheduled-task-configuration)
8. [Git Operations Requiring Human Action](#8-git-operations-requiring-human-action)
9. [Troubleshooting Common Failures](#9-troubleshooting-common-failures)

---

## 1. Fresh Workspace Stand-Up

**When:** Re-deploying the demo on a new workspace, or rebuilding from scratch.

**Prerequisites (human must verify):**
- [ ] Workspace is on AWS (Lakebase GA requirement per DECISION-CLOUD)
- [ ] Compute policy allows DBR 17.1+ or serverless (native `ST_*` + H3)
- [ ] Unity Catalog is enabled on the workspace
- [ ] Catalog `cdm_tmforum` exists with CREATE SCHEMA privilege for the deployer
- [ ] Git credential configured ("skhage-github" OAuth, user: skhage)

**Steps:**
1. Clone the repo:
   ```
   runGit(clone, path=/Workspace/Users/<user>/copper-retirement,
          url=<repo-url>, provider=gitHub)
   ```
2. Run DAB deployment (see Section 2).
3. Execute data generation in order (see Section 3).
4. Set up Lakebase task board (see Section 4).
5. Deploy apps (see Section 5).
6. Configure scheduled tasks (see Section 7).

---

## 2. DAB Deployment

**What it creates:** Schemas in `cdm_tmforum` catalog:
- `copper_retirement` — Synthetic/pipeline tables
- `bronze` — Raw landed sources
- `silver` — Cleaned, conformed, H3-indexed
- `gold` — Business-ready aggregates
- `ml` — Model training/feature tables
- `ops` — Lakebase-synced operational tables
- `agents` — Agent definitions and eval sets

**Config files:**
- `databricks.yml` — Bundle root (targets: `dev`)
- `bundle/resources/unity_catalog.yml` — Schema definitions

**Manual steps:**
1. Verify catalog exists:
   ```sql
   SHOW SCHEMAS IN cdm_tmforum;
   ```
2. Deploy from the repo root:
   ```bash
   cd /Workspace/Users/<user>/copper-retirement
   databricks bundle validate --target dev
   databricks bundle deploy --target dev
   ```
3. Verify schemas were created:
   ```sql
   SHOW SCHEMAS IN cdm_tmforum LIKE 'copper*';
   SHOW SCHEMAS IN cdm_tmforum LIKE 'bronze';
   SHOW SCHEMAS IN cdm_tmforum LIKE 'silver';
   SHOW SCHEMAS IN cdm_tmforum LIKE 'gold';
   ```

**Known issues:**
- If `P0-CREATE-SCHEMA` was already run manually (agent executed
  `CREATE SCHEMA IF NOT EXISTS`), the DAB deploy will succeed but won't
  overwrite the schema comments. Run
  `COMMENT ON SCHEMA cdm_tmforum.<name> IS '<comment>'` manually if needed.
- The `dev` target is the only target currently configured. A `staging` target
  is planned for future phases.

---

## 3. Data Generation Execution Order

**CRITICAL: Order matters.** Data generators have FK dependencies on parent
tables and geographic data. Executing out of order produces orphaned FK values
or missing spatial joins.

### Dependency Chain

```
  Phase 0 Foundation
  ├── P0-CREATE-SCHEMA       (schemas must exist first)
  ├── FIX-COORDINATES        (geographic_site + geographic_address coordinates)
  │   └── P0-FIX-COORDINATES-CELL7  (H3 function fix for Cell 7)
  ├── P0-POPULATE-H3-INDEXES (H3 columns on address/device/CFS tables)
  │   └── depends on: FIX-COORDINATES, P0-CREATE-SCHEMA
  ├── P0-DATAGEN-COPPER-EXECUTE
  │   └── depends on: P0-CREATE-SCHEMA, FIX-COORDINATES
  ├── P0-DATAGEN-COMMODITY-EXECUTE
  │   └── depends on: P0-CREATE-SCHEMA
  ├── P0-DATAGEN-REG-EXECUTE
  │   └── depends on: P0-CREATE-SCHEMA
  ├── P0-DATAGEN-WIRECENTER-EXECUTE
  │   └── depends on: P0-CREATE-SCHEMA, FIX-COORDINATES
  ├── P0-DATAGEN-CONTRACTOR-EXECUTE  [PENDING]
  │   └── depends on: P0-CREATE-SCHEMA, FIX-COORDINATES
  └── P0-DATAGEN-DIGSAFE-EXECUTE     [PENDING]
      └── depends on: P0-CREATE-SCHEMA, FIX-COORDINATES

  Phase 2 Geospatial
  ├── P2-H3          (H3-index all layers)
  │   └── depends on: FIX-COORDINATES
  └── P2-JOIN        (H3 spatial joins)  [IN PROGRESS]
      └── depends on: P2-H3

  Phase 3 Pipelines
  └── P3-DLP         (Lakeflow declarative pipeline)
      └── depends on: P2-JOIN

  Phase 4 ML
  ├── P4-RISK-COMPOSITE-TARGET  (depends on: FIX-COORDINATES)
  ├── P4-RISK-MODEL-TRAIN       (depends on: P4-RISK-COMPOSITE-TARGET)
  ├── P4-RISK-FAIRNESS          (depends on: P4-RISK-MODEL-TRAIN)
  └── P4-RISK-CHAMPION-CHALLENGER (depends on: P4-RISK-FAIRNESS)
```

### FK Constraint Rules (from CEO directive)

All synthetic data MUST comply with existing data models:
- `customer_id` values from `tmf_customer.customer`
- `geographic_address_id` from `tmf_shared.geographic_address`
- `bp_agreement_id` from `tmf_businesspartner.bp_agreement`
- `physical_device_id` from `tmf_enterprise.physical_device`

Never generate FK values that don't exist in the referenced parent table.

### H3 Function Compatibility

**Important:** Serverless compute uses `h3_longlatash3(lon, lat, resolution)`,
NOT `h3_latlng_to_cell(lat, lon, resolution)`. Note the argument order swap
(longitude first). CEO directive (2026-09-11) documents this fix.

---

## 4. Lakebase Task Board Setup

**Project:** `copper-task-board` (already provisioned)

**If rebuilding from scratch:**
1. Create the Lakebase project:
   ```python
   from databricks.sdk import WorkspaceClient
   w = WorkspaceClient()
   project = w.postgres.create_project(name="copper-task-board")
   ```
2. Create the schema tables (`agent_tasks`, `status_updates`,
   `ceo_directives`, `decisions`) using the DDL stored in the project.
3. Seed initial task data from BUILD-PLAN.md work items.
4. Verify agent connectivity:
   ```python
   endpoint = "projects/copper-task-board/branches/production/endpoints/primary"
   host = "ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com"
   # Test with: SELECT COUNT(*) FROM agent_tasks;
   ```

**Ongoing maintenance:**
- All agents read/write via `psycopg` + SDK token auth.
- Task board is the single source of truth for task status.
- `.assistant_instructions.md` retains role definitions and data inventory
  only (frozen — not updated for task progress).

---

## 5. App Deployment

**Five apps in `/apps/`:**

| App | Directory | Status | Dependencies |
|-----|-----------|--------|-------------|
| Copper Map | `apps/copper-map/` | Scaffolded | H3 data, geographic tables |
| Retirement Plan | `apps/retirement-plan/` | Scaffolded | Gold readiness table, ML risk scores |
| Dig Triage | `apps/dig-triage/` | Scaffolded | Dig-safe incidents, geospatial data |
| Regulatory Assistant | `apps/regulatory-assistant/` | Scaffolded | Regulatory corpus, RAG agent |
| Commodity Dashboard | `apps/commodity-dashboard/` | Scaffolded | Commodity price data, forecasts |

**Deployment steps (per app):**
1. Verify data dependencies are populated (tables exist, non-empty).
2. Deploy via Databricks Apps:
   ```bash
   databricks apps create <app-name>
   databricks apps deploy <app-name> --source-code-path apps/<dir>/
   ```
3. Configure app resources in `app.yaml` (SQL warehouse, secrets).
4. Validate OAuth configuration for data access.
5. @designer must review before demo-readiness sign-off.

**Brand requirements (CEO directive 2026-09-12):**
- Lakelink Fiber brand identity: Primary #FF3621, Secondary #1B3139,
  Accent #00A972, Surface #F9F7F4
- Typography: Inter/system sans-serif
- Icons: Lucide (1.5px stroke)
- All apps must pass @designer UX review.

---

## 6. ML Model Registration & Serving

**Phase 4 ML pipeline (not yet fully deployed):**

1. **Feature engineering** (P4-RISK-FEATURES — completed):
   - Feature tables written to `cdm_tmforum.ml`
2. **Model training** (P4-RISK-MODEL-TRAIN — pending):
   - GBT/XGBoost risk classifier
   - MLflow experiment tracking
   - Manual step: verify MLflow experiment exists, check compute has
     ML Runtime
3. **Fairness testing** (P4-RISK-FAIRNESS — pending):
   - Sub-demographic slicing by device_type, geography, service_type,
     customer segment
4. **Model registry** (P4-RISK-CHAMPION-CHALLENGER — pending):
   - UC Model Registry with @prod/@challenger aliases
   - Manual step: human must approve champion promotion
5. **Serving** (P4-SERVE — not yet assigned):
   - Model Serving endpoint creation
   - Lakehouse Monitoring on inference table
   - Manual step: configure endpoint scaling, approve cost

---

## 7. Scheduled Task Configuration

**Eight agent scheduled tasks (all active as of 2026-09-11):**

| Agent | Task ID | Cadence |
|-------|---------|--------|
| @data-planner | `b27c43599c28466498a1ce15a4487cca` | Daily |
| @data-engineer | `218f6f9ca64749ce901854ea973551f8` | Daily |
| @data-analyst | `14c120a93b9d408b9c840a467714745b` | Daily |
| @ml-engineer | `83814f8ee58042dbbbc5a137dac76824` | Daily |
| @pm | `f11e97a7c161400e80a06f3ac8fb0b4f` | Daily |
| @qa | `056bf86924174fe5be1636b4f4f214bc` | Daily |
| @devops | `cb363630d10b444f9a75bc1c8e10f661` | Daily |
| @app-developer | `d175baccbb80467595244fe07bb6fae4` | Daily |
| @designer | `f169a1fb28dc4cff948590d6bb2cc3d5` | Every 3 days |

**To reconfigure (human action):**
- Scheduled tasks are managed via the Genie Code automations panel.
- Navigate to: `/editor/folders/workspace?mode=chat&panel=automations`
- Each task has the agent identity and protocol in its system prompt.
- DML execution IS approved for scheduled runs (CEO directive 2026-09-11).

---

## 8. Git Operations Requiring Human Action

### 8.1 Branch Merges

Agents cannot merge branches via the `runGit` API. Merges require:
- **Option A:** Human opens the Git modal in the Repos UI:
  `https://fevm-cmegdemos.cloud.databricks.com/browse?o=7474656585748611&openGit=2316637929217639`
- **Option B:** Human creates and merges a GitHub PR.

### 8.2 Hard Resets

If `main` is broken and needs a hard reset:
1. Human opens the 3-dot overflow menu in the Repos UI.
2. Select "Reset to remote" to force-sync with GitHub.
3. **WARNING:** This discards all local changes.

### 8.3 Conflict Resolution (Escalated)

When an agent logs a `blocked` task due to merge conflicts:
1. Check the agent's `status_notes` in Lakebase for the conflicted files.
2. Open the Git modal and resolve manually, OR
3. @devops can attempt resolution via `runGit` API (`conflict_info` →
   `accept_file` → `continue`).

### 8.4 Stale Branch Cleanup

Branches to review (as of 2026-09-12):
- `polly/p0-thin-slice` — Legacy, likely mergeable
- `polly/p0-uc` — Legacy UC setup
- `polly/production-hardening` — Review for merge
- `polly/synthetic-data-foundation-codex-v2` — Review for merge
- `copper-task-board-slack-ui` — Slack UI feature
- `research-files` — Archive candidate

Human should delete branches via GitHub after confirming content is in `main`.

---

## 9. Troubleshooting Common Failures

### Lakebase Connection Fails
```
ModuleNotFoundError: No module named 'psycopg'
```
**Fix:** Run `pip install psycopg[binary]` before connecting. SDK restart
may be needed after `databricks-sdk` upgrade.

### H3 Function Error
```
AnalysisException: function h3_latlng_to_cell not found
```
**Fix:** Use `h3_longlatash3(longitude, latitude, resolution)` on serverless.
Note: longitude comes first.

### DAB Deploy Fails with Permission Error
```
PermissionDenied: User does not have CREATE SCHEMA on catalog cdm_tmforum
```
**Fix:** Human must grant:
```sql
GRANT CREATE SCHEMA ON CATALOG cdm_tmforum TO `<user>`;
```

### Agent Scheduled Task Not Firing
**Check:** Navigate to automations panel. Verify the task is enabled and the
schedule is active. Per CEO directive (2026-09-11): all 8 tasks confirmed
active.

### Git Authentication Error
**Fix:** Run `runGit(list_credentials)` to identify the failing credential.
Verify "skhage-github" OAuth credential is default for gitHub provider.
See `BRANCH_STRATEGY.md` Section 3 for the full protocol.
