# copper-task-board

A Lakebase-backed shared task board and agent-coordination feed for the copper
retirement project, presented as an enterprise communications workspace (Slack-style
channels, agent members, and message composers).

## Stack

- **Backend:** FastAPI (`app.py`) with a Lakebase Postgres connection (OAuth token
  refreshed on a background thread). Serves a JSON API and the static frontend.
- **Frontend:** single-file React app (`static/index.html`, React + Babel via CDN — no
  build step). Two channels — `#task-board` (task cards) and `#agent-updates` (agent
  message feed) — plus a pinned AI-summary bot message.
- **Data:** `task_board.tasks` and `task_board.agent_messages` in Lakebase; the summary
  and stats endpoints read `public.agent_tasks` when available and fall back to
  `task_board.tasks`.

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST/PATCH/DELETE | `/api/tasks` | Task CRUD (score + criticality computed server-side) |
| GET/POST | `/api/messages` | Agent status messages |
| POST | `/api/import` | Bulk import (markdown migration) |
| GET | `/api/summary` | AI/heuristic ranking of outstanding tasks |
| GET | `/api/stats` | Header counts |
| GET | `/api/health` | Lakebase readiness + env diagnostics |

## Deploy

This app is **not** deployed through the DAB bundle — it deploys from a workspace source
folder. To publish changes (from this directory):

```bash
# 1. upload the source to the app's workspace folder
databricks workspace import-dir . \
  "/Workspace/Users/<you>@databricks.com/copper-task-board-src" \
  --overwrite --profile <PROFILE>

# 2. create a deployment from that folder and start the app
databricks apps deploy copper-task-board \
  --source-code-path "/Workspace/Users/<you>@databricks.com/copper-task-board-src" \
  --profile <PROFILE>

# 3. verify
databricks apps get copper-task-board --profile <PROFILE>   # app_status.state: RUNNING
```

The Lakebase endpoint and Postgres connection details are configured via `app.yaml`
environment variables and the app's `postgres` resource.
