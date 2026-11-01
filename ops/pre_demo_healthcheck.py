#!/usr/bin/env python3
"""
Copper Retirement — Pre-Demo Health Check
==========================================
One-command script to verify all critical demo components are live.
Run from any Databricks notebook cell or terminal:
    %run ./ops/pre_demo_healthcheck   (path relative to the bundle/project root)

Config (env vars, default to bundle variables catalog_name/schema_name):
    COPPER_CATALOG, COPPER_SCHEMA, COPPER_VS_ENDPOINT
    COPPER_CORE_APPS     comma list, default "retirement-plan" (bundle deploys: retirement-plan-<target>)
    COPPER_SUPPORT_APPS  comma list, default "copper-task-board" (bundle deploys: copper-task-board-<target>)
    COPPER_PIPELINE_ID   pipeline id; if unset, looked up by COPPER_PIPELINE_NAME
    COPPER_PIPELINE_NAME default "copper-retirement-pipeline" (bundle deploys: copper-retirement-pipeline-<target>)

Outputs GREEN / YELLOW / RED per component:
  1. Apps        — unified accelerator app (core) is ACTIVE; copper-task-board (support)
  2. Endpoints   — Serving endpoints are READY
  3. Pipeline    — DLP pipeline last successful run < 48h
  4. Lakebase    — Task-board tables are accessible
  5. VectorSearch— Regulatory index is ONLINE with rows (optional)
  6-9. MV freshness, inference table, Lakebase sync, citation invariant
  10. Release numbers — live PARTNER-PLAYBOOK §0/§2e/§5b-2 figures as a markdown table
      (env: COPPER_APP_SP_ID, COPPER_RESTRICTED_SOURCE_IDS, COPPER_LEGACY_APPS)

Author: @devops | Created: 2026-09-21
"""

import sys
import subprocess
import importlib.metadata as _md
from datetime import datetime, timezone
from enum import Enum

# ---------------------------------------------------------------------------
# 0. Ensure SDK is recent enough for Lakebase credential generation
# ---------------------------------------------------------------------------
try:
    _v = _md.version("databricks-sdk")
    _need_upgrade = tuple(int(x) for x in _v.split(".")[:3]) < (0, 118, 0)
except _md.PackageNotFoundError:
    _need_upgrade = True
if _need_upgrade:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--upgrade",
         "databricks-sdk>=0.118.0", "--quiet"]
    )
try:
    import psycopg  # noqa: F401
except ImportError:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "psycopg[binary]", "--quiet"]
    )

# ---------------------------------------------------------------------------
# Imports (after installs)
# ---------------------------------------------------------------------------
import os
import psycopg
from databricks.sdk import WorkspaceClient

# Parameterized config (ACC-DE-PARAMETERIZE): override via env vars for partner workspaces
CATALOG = os.environ.get("COPPER_CATALOG", "cdm_tmforum")
SCHEMA = os.environ.get("COPPER_SCHEMA", "copper_retirement")
FQ = f"{CATALOG}.{SCHEMA}"


class Status(Enum):
    GREEN = "\033[92m GREEN \033[0m"
    YELLOW = "\033[93mYELLOW\033[0m"
    RED = "\033[91m  RED  \033[0m"


def _banner(label: str):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")


def _row(name: str, status: Status, detail: str = ""):
    tag = status.value
    print(f"  [{tag}]  {name:<40} {detail}")


# ===================================================================
# 1. APPS — 2-app end state (DEC-ACCEL-UNIFIED-APP): unified accelerator app
#    (tabs Map/Risk, Plan, Dig Triage, Regulatory, Commodity) + ops task board.
#    Retired apps (copper-map, dig-triage, regulatory-assistant,
#    commodity-dashboard, lakelink-ra-review) are no longer checked.
# ===================================================================
def _env_list(var: str, default: str) -> list:
    return [x.strip() for x in os.environ.get(var, default).split(",") if x.strip()]


CORE_APPS = _env_list("COPPER_CORE_APPS", "retirement-plan")          # unified accelerator app
SUPPORT_APPS = _env_list("COPPER_SUPPORT_APPS", "copper-task-board")  # ops: agent task board


def check_apps(w: WorkspaceClient) -> Status:
    _banner("1/8  APPS")
    worst = Status.GREEN
    for name in CORE_APPS + SUPPORT_APPS:
        is_core = name in CORE_APPS
        try:
            app = w.apps.get(name)
            compute = getattr(app, "compute_status", None)
            state_str = str(compute.state).split(".")[-1] if compute else "UNKNOWN"
            deploy = app.active_deployment
            dep_state = (
                str(deploy.status.state).split(".")[-1]
                if deploy and deploy.status else "NO_DEPLOY"
            )
            if state_str == "ACTIVE" and dep_state == "SUCCEEDED":
                s = Status.GREEN
            elif state_str == "ACTIVE":
                s = Status.YELLOW
            else:
                s = Status.RED
        except Exception as exc:
            s = Status.RED
            state_str = f"ERROR: {exc}"
            dep_state = "-"

        label = f"{name} {'[CORE]' if is_core else '[SUPPORT]'}"
        _row(label, s, f"compute={state_str}  deploy={dep_state}")

        # Only core apps affect overall status
        if is_core:
            if s == Status.RED:
                worst = Status.RED
            elif s == Status.YELLOW and worst != Status.RED:
                worst = Status.YELLOW
    return worst


# ===================================================================
# 2. SERVING ENDPOINTS — key endpoints must be READY
# ===================================================================
CORE_ENDPOINTS = [
    "copper-retirement-risk",  # Risk model
]


def check_endpoints(w: WorkspaceClient) -> Status:
    _banner("2/8  SERVING ENDPOINTS")
    worst = Status.GREEN
    for name in CORE_ENDPOINTS:
        try:
            ep = w.serving_endpoints.get(name)
            ready = str(ep.state.ready).split(".")[-1] if ep.state else "UNKNOWN"
            if ready == "READY":
                s = Status.GREEN
            else:
                s = Status.RED
        except Exception as exc:
            s = Status.RED
            ready = f"ERROR: {exc}"
        _row(name, s, f"ready={ready}")
        if s.name == "RED":
            worst = Status.RED
        elif s.name == "YELLOW" and worst != Status.RED:
            worst = Status.YELLOW
    return worst


# ===================================================================
# 3. DLP PIPELINE — last successful run < 48 hours
# ===================================================================
# Legacy copper-retirement-dlp (3d0576c0) is deprecated and no longer checked
# (ACC-DEVOPS-LEGACY-DLP-DELETE). Only the bundle-managed pipeline is checked.
PIPELINE_NAME = os.environ.get("COPPER_PIPELINE_NAME", "copper-retirement-pipeline")
PIPELINE_ID = os.environ.get("COPPER_PIPELINE_ID", "")
MAX_AGE_HOURS = 48


def _resolve_pipeline_id(w: WorkspaceClient) -> str:
    if PIPELINE_ID:
        return PIPELINE_ID
    for p in w.pipelines.list_pipelines(filter=f"name LIKE '{PIPELINE_NAME}'"):
        if p.name == PIPELINE_NAME:
            return p.pipeline_id
    raise LookupError(f"pipeline '{PIPELINE_NAME}' not found; set COPPER_PIPELINE_ID or COPPER_PIPELINE_NAME")


def check_pipelines(w: WorkspaceClient) -> Status:
    _banner("3/8  DLP PIPELINES")
    worst = Status.GREEN
    for pname in [PIPELINE_NAME]:
        try:
            pid = _resolve_pipeline_id(w)
            updates = w.pipelines.list_updates(pipeline_id=pid)
            if updates and updates.updates:
                latest = updates.updates[0]
                state = str(latest.state).split(".")[-1] if latest.state else "UNKNOWN"
                ts = None
                if latest.creation_time:
                    ts = datetime.fromtimestamp(
                        latest.creation_time / 1000, tz=timezone.utc
                    )
                    age_h = (
                        datetime.now(tz=timezone.utc) - ts
                    ).total_seconds() / 3600
                else:
                    age_h = 999

                if state == "COMPLETED" and age_h <= MAX_AGE_HOURS:
                    s = Status.GREEN
                elif state == "COMPLETED":
                    s = Status.YELLOW  # completed but stale
                elif state in ("RUNNING", "WAITING_FOR_RESOURCES"):
                    s = Status.YELLOW
                else:
                    s = Status.RED  # FAILED / CANCELED
                detail = f"state={state}  age={age_h:.1f}h"
            else:
                s = Status.RED
                detail = "no updates found"
        except Exception as exc:
            s = Status.RED
            detail = f"ERROR: {exc}"

        _row(pname, s, detail)
        if s.name == "RED":
            worst = Status.RED
        elif s.name == "YELLOW" and worst != Status.RED:
            worst = Status.YELLOW
    return worst


# ===================================================================
# 4. LAKEBASE — task-board tables accessible
# ===================================================================
LAKEBASE_ENDPOINT = (
    "projects/copper-task-board/branches/production/endpoints/primary"
)
LAKEBASE_HOST = (
    "ep-rough-bar-d229503i.database.us-east-1.cloud.databricks.com"
)
EXPECTED_TABLES = ["agent_tasks", "ceo_directives", "decisions", "status_updates"]


def check_lakebase(w: WorkspaceClient) -> Status:
    _banner("4/8  LAKEBASE")
    try:
        user = w.current_user.me().user_name
        token = w.postgres.generate_database_credential(
            endpoint=LAKEBASE_ENDPOINT
        ).token
        conn = psycopg.connect(
            host=LAKEBASE_HOST,
            dbname="databricks_postgres",
            user=user,
            password=token,
            sslmode="require",
        )
        conn.autocommit = True
        cur = conn.cursor()
    except Exception as exc:
        _row("Lakebase connection", Status.RED, f"ERROR: {exc}")
        return Status.RED

    _row("Lakebase connection", Status.GREEN, "connected")
    worst = Status.GREEN
    for tbl in EXPECTED_TABLES:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            cnt = cur.fetchone()[0]
            s = Status.GREEN if cnt > 0 else Status.YELLOW
            _row(f"  table: {tbl}", s, f"{cnt} rows")
        except Exception as exc:
            s = Status.RED
            _row(f"  table: {tbl}", s, f"ERROR: {exc}")
        if s.name == "RED":
            worst = Status.RED
        elif s.name == "YELLOW" and worst != Status.RED:
            worst = Status.YELLOW

    cur.close()
    conn.close()
    return worst


# ===================================================================
# 5. VECTOR SEARCH — OPTIONAL (DEC-VS-OPTIONAL). Never FAILs the healthcheck:
#    problems are WARN (YELLOW) because default retrieval is the UC TVF
#    search_regulatory_chunks. Unset COPPER_VS_ENDPOINT ("") to skip entirely.
# ===================================================================
VS_ENDPOINT = os.environ.get("COPPER_VS_ENDPOINT", "cmeg-demos-vs").strip()
VS_INDEX = f"{FQ}." + (os.environ.get("COPPER_VS_INDEX", "").strip() or "regulatory_doc_chunks_vs_index")


def check_vector_search(w: WorkspaceClient) -> Status:
    _banner("5/8  VECTOR SEARCH (optional)")
    if not VS_ENDPOINT:
        _row("Vector Search", Status.GREEN, "disabled (optional); TVF retrieval in use")
        return Status.GREEN
    worst = _check_vector_search_inner(w)
    # DEC-VS-OPTIONAL: downgrade RED to WARN so a missing/offline VS never fails the run.
    return Status.YELLOW if worst == Status.RED else worst


def _check_vector_search_inner(w: WorkspaceClient) -> Status:
    worst = Status.GREEN

    # Endpoint
    try:
        ep = w.vector_search_endpoints.get_endpoint(VS_ENDPOINT)
        ep_state = (
            str(ep.endpoint_status.state).split(".")[-1]
            if ep.endpoint_status else "UNKNOWN"
        )
        s = Status.GREEN if ep_state == "ONLINE" else Status.RED
        _row(f"Endpoint: {VS_ENDPOINT}", s, f"state={ep_state}")
    except Exception as exc:
        s = Status.RED
        _row(f"Endpoint: {VS_ENDPOINT}", s, f"ERROR: {exc}")
    if s.name == "RED":
        worst = Status.RED

    # Index
    try:
        idx = w.vector_search_indexes.get_index(index_name=VS_INDEX)
        idx_ready = idx.status.ready if idx.status else False
        row_count = idx.status.indexed_row_count if idx.status else 0
        if idx_ready and row_count and row_count > 0:
            s = Status.GREEN
        elif idx_ready:
            s = Status.YELLOW
        else:
            s = Status.RED
        _row(f"Index: {VS_INDEX}", s, f"ready={idx_ready}  rows={row_count}")
    except Exception as exc:
        s = Status.RED
        _row(f"Index: {VS_INDEX}", s, f"ERROR: {exc}")
    if s.name == "RED":
        worst = Status.RED
    elif s.name == "YELLOW" and worst != Status.RED:
        worst = Status.YELLOW

    return worst


# ===================================================================
# 6. MV FRESHNESS — all 8 DLP materialized views < 24h old
# ===================================================================
DLP_MVS = [
    "bronze_copper_devices",
    "bronze_copper_services",
    "bronze_dig_safe_incidents",
    "gold_contractor_scorecard",
    "gold_retirement_executive_summary",
    "gold_wire_center_scorecard",
    "silver_copper_plant_enriched",
    "silver_device_service_impact",
]
MV_MAX_AGE_HOURS = 24


def check_mv_freshness(w: WorkspaceClient) -> Status:
    _banner("6/8  MV FRESHNESS")
    worst = Status.GREEN
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        rows = spark.sql(
            "SELECT table_name, last_altered, "
            "TIMESTAMPDIFF(HOUR, last_altered, current_timestamp()) as age_h "
            f"FROM {CATALOG}.information_schema.tables "
            f"WHERE table_schema = '{SCHEMA}' "
            "AND table_type = 'MATERIALIZED_VIEW' "
            "ORDER BY table_name"
        ).collect()
    except Exception as exc:
        _row("Spark query", Status.RED, f"ERROR: {exc}")
        return Status.RED

    found = {r.table_name: r.age_h for r in rows}
    for mv in DLP_MVS:
        age = found.get(mv)
        if age is None:
            s = Status.RED
            _row(mv, s, "MISSING from information_schema")
        elif age > MV_MAX_AGE_HOURS:
            s = Status.RED
            _row(mv, s, f"age={age}h > {MV_MAX_AGE_HOURS}h — STALE")
        else:
            s = Status.GREEN
            _row(mv, s, f"age={age}h")
        if s.name == "RED":
            worst = Status.RED
        elif s.name == "YELLOW" and worst != Status.RED:
            worst = Status.YELLOW
    return worst


# ===================================================================
# 7. INFERENCE TABLE — risk_model_inference_payload not stale
# ===================================================================
INFERENCE_TABLE = f"{FQ}.risk_model_inference_payload"
INFERENCE_MAX_AGE_HOURS = 48


def check_inference_table(w: WorkspaceClient) -> Status:
    _banner("7/8  INFERENCE TABLE")
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        row = spark.sql(
            f"SELECT COUNT(*) as cnt, "
            f"MAX(request_time) as latest, "
            f"COALESCE(TIMESTAMPDIFF(HOUR, MAX(request_time), current_timestamp()), 9999) as age_h "
            f"FROM {INFERENCE_TABLE}"
        ).collect()[0]
    except Exception as exc:
        _row(INFERENCE_TABLE, Status.RED, f"ERROR: {exc}")
        return Status.RED

    if row.cnt == 0:
        s = Status.YELLOW
        _row("Inference payload", s, "0 rows — no inferences logged")
    elif row.age_h > INFERENCE_MAX_AGE_HOURS:
        s = Status.YELLOW
        _row("Inference payload", s, f"latest={row.latest}  age={row.age_h}h — stale")
    else:
        s = Status.GREEN
        _row("Inference payload", s, f"{row.cnt} rows  latest={row.latest}  age={row.age_h}h")
    return s


# ===================================================================
# 8. LAKEBASE SYNC — copper_app tables match UC source counts
# ===================================================================
# Maps Lakebase copper_app table → UC source table (for row-count sync check)
SYNC_PAIRS = {
    "wire_center_scorecard": f"{FQ}.gold_wire_center_scorecard",
    "gold_wave_schedule": f"{FQ}.gold_wave_schedule",
    "gold_contractor_assignment_plan": f"{FQ}.gold_contractor_assignment_plan",
    "gold_copper_recovery_schedule": f"{FQ}.gold_copper_recovery_schedule",
    "gold_reroute_options": f"{FQ}.gold_reroute_options",
    "device_risk_map": f"{FQ}.copper_risk_predictions",
    "executive_summary": f"{FQ}.gold_retirement_executive_summary",
    "contractor_scorecard": f"{FQ}.gold_contractor_scorecard",
}


def check_lakebase_sync(w: WorkspaceClient) -> Status:
    _banner("8/8  LAKEBASE SYNC")
    # Connect to Lakebase
    try:
        user = w.current_user.me().user_name
        token = w.postgres.generate_database_credential(
            endpoint=LAKEBASE_ENDPOINT
        ).token
        lb_conn = psycopg.connect(
            host=LAKEBASE_HOST,
            dbname="databricks_postgres",
            user=user,
            password=token,
            sslmode="require",
        )
        lb_conn.autocommit = True
        lb_cur = lb_conn.cursor()
    except Exception as exc:
        _row("Lakebase connection", Status.RED, f"ERROR: {exc}")
        return Status.RED

    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
    except Exception as exc:
        _row("Spark session", Status.RED, f"ERROR: {exc}")
        lb_cur.close()
        lb_conn.close()
        return Status.RED

    worst = Status.GREEN
    for lb_table, uc_table in SYNC_PAIRS.items():
        try:
            lb_cur.execute(f"SELECT COUNT(*) FROM copper_app.{lb_table}")
            lb_cnt = lb_cur.fetchone()[0]
        except Exception:
            lb_cnt = -1

        try:
            uc_cnt = spark.sql(f"SELECT COUNT(*) as cnt FROM {uc_table}").collect()[0].cnt
        except Exception:
            uc_cnt = -1

        if lb_cnt == -1 or uc_cnt == -1:
            s = Status.RED
            _row(lb_table, s, f"lb={lb_cnt}  uc={uc_cnt} — query error")
        elif lb_cnt == uc_cnt:
            s = Status.GREEN
            _row(lb_table, s, f"synced  rows={lb_cnt}")
        elif lb_cnt == 0 and uc_cnt > 0:
            s = Status.RED
            _row(lb_table, s, f"lb=0  uc={uc_cnt} — NOT SYNCED")
        else:
            s = Status.YELLOW
            drift_pct = abs(lb_cnt - uc_cnt) / max(uc_cnt, 1) * 100
            _row(lb_table, s, f"lb={lb_cnt}  uc={uc_cnt}  drift={drift_pct:.1f}%")

        if s.name == "RED":
            worst = Status.RED
        elif s.name == "YELLOW" and worst != Status.RED:
            worst = Status.YELLOW

    lb_cur.close()
    lb_conn.close()
    return worst


# ===================================================================
# 9. CITATION PROVENANCE INVARIANT (ACC-QA-CHECKLIST-INVARIANT, @qa)
#    is_synthetic = FALSE  =>  source/citation URL IS NOT NULL.
#    Any violation is RED: a non-synthetic regulatory fact without an
#    official URL breaks the charter citation rule.
# ===================================================================
UC_INVARIANTS = {
    # table -> SQL expression for the URL column
    f"{FQ}.regulatory_doc_chunks": "source_url",
    f"{FQ}.jurisdiction_requirements_cited": "coalesce(citation_url, official_url)",
}
LB_INVARIANTS = {
    "copper_app.regulatory_checklist_status": "source_url",
}


def check_citation_invariant(w: WorkspaceClient) -> Status:
    _banner("9/9  CITATION PROVENANCE (is_synthetic=FALSE => URL)")
    worst = Status.GREEN
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        for tbl, url_expr in UC_INVARIANTS.items():
            try:
                r = spark.sql(
                    f"SELECT count(*) FILTER (WHERE NOT coalesce(is_synthetic, false)) AS real_rows, "
                    f"count(*) FILTER (WHERE NOT coalesce(is_synthetic, false) "
                    f"AND ({url_expr} IS NULL OR trim({url_expr}) = '')) AS bad FROM {tbl}"
                ).collect()[0]
                s = Status.GREEN if r.bad == 0 else Status.RED
                _row(tbl.split(".")[-1], s, f"real={r.real_rows}  violations={r.bad}")
            except Exception as exc:
                s = Status.RED
                _row(tbl.split(".")[-1], s, f"ERROR: {exc}")
            if s == Status.RED:
                worst = Status.RED
    except Exception as exc:
        _row("Spark session", Status.RED, f"ERROR: {exc}")
        worst = Status.RED
    try:
        user = w.current_user.me().user_name
        token = w.postgres.generate_database_credential(endpoint=LAKEBASE_ENDPOINT).token
        with psycopg.connect(host=LAKEBASE_HOST, dbname="databricks_postgres", user=user,
                             password=token, sslmode="require", autocommit=True) as c:
            cur = c.cursor()
            for tbl, url_col in LB_INVARIANTS.items():
                cur.execute(
                    f"SELECT count(*) FILTER (WHERE NOT coalesce(is_synthetic, false)), "
                    f"count(*) FILTER (WHERE NOT coalesce(is_synthetic, false) "
                    f"AND ({url_col} IS NULL OR trim({url_col}) = '')) FROM {tbl}"
                )
                real_rows, bad = cur.fetchone()
                s = Status.GREEN if bad == 0 else Status.RED
                _row(tbl, s, f"real={real_rows}  violations={bad}")
                if s == Status.RED:
                    worst = Status.RED
    except Exception as exc:
        _row("Lakebase invariant", Status.RED, f"ERROR: {exc}")
        worst = Status.RED
    return worst


# ===================================================================
# 10. RELEASE NUMBERS (ACC-DE-HEALTHCHECK-RELEASE-NUMBERS)
#     Live, SQL-generated figures for PARTNER-PLAYBOOK §0 / §2e / §5b-2.
#     Informational: never changes overall status unless queries error (YELLOW).
#     Prints a markdown table @pm can paste instead of hand-typing numbers.
# ===================================================================
APP_SP_ID = os.environ.get("COPPER_APP_SP_ID", "d96a80a5-cf49-4947-b518-164cd950f872")
# Apps counted for the 2-app gate: core + support + retired legacy apps still deployed
PROJECT_APPS = CORE_APPS + SUPPORT_APPS + _env_list(
    "COPPER_LEGACY_APPS", "copper-map,dig-triage,regulatory-assistant,commodity-dashboard,lakelink-ra-review")
RESTRICTED_SOURCE_IDS = [x.strip() for x in os.environ.get("COPPER_RESTRICTED_SOURCE_IDS", "IND-CGA-BP21").split(",") if x.strip()]


def release_numbers(w: WorkspaceClient) -> list:
    """Return [(section, metric, value)] from live queries."""
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    out = []
    restricted = ", ".join("'" + s.replace("'", "''") + "'" for s in RESTRICTED_SOURCE_IDS) or "''"

    def one(sql):
        return spark.sql(sql).collect()[0]

    def add(section, metric, fn):
        try:
            out.append((section, metric, fn()))
        except Exception as exc:
            out.append((section, metric, f"ERROR: {str(exc)[:120]}"))

    # §0 / §2e: regulatory corpus
    def _chunks():
        r = one(
            f"SELECT count(*) total, "
            f"count(*) FILTER (WHERE NOT coalesce(is_synthetic,false) AND coalesce(source_id,'') NOT IN ({restricted})) public_real, "
            f"count(*) FILTER (WHERE coalesce(source_id,'') IN ({restricted})) restricted_cga, "
            f"count(*) FILTER (WHERE coalesce(is_synthetic,false)) synthetic, "
            f"count(DISTINCT source_id) FILTER (WHERE NOT coalesce(is_synthetic,false) AND coalesce(source_id,'') NOT IN ({restricted})) public_sources "
            f"FROM {FQ}.regulatory_doc_chunks")
        return r
    try:
        c = _chunks()
        out += [("§0/§2e", "regulatory_doc_chunks total", c.total),
                ("§0/§2e", "  real public chunks", c.public_real),
                ("§0/§2e", "  real public source_ids", c.public_sources),
                ("§0/§2e", "  restricted (CGA) chunks", c.restricted_cga),
                ("§0/§2e", "  synthetic chunks", c.synthetic),
                ("§0/§2e", "R2 delete-predicate rows (restricted OR synthetic)", c.restricted_cga + c.synthetic),
                ("§0/§2e", "  chunks left after R2 delete", c.total - c.restricted_cga - c.synthetic)]
    except Exception as exc:
        out.append(("§0/§2e", "regulatory_doc_chunks", f"ERROR: {str(exc)[:120]}"))

    # §2e: cited jurisdiction matrix
    add("§2e", "jurisdiction_requirements_cited rows",
        lambda: one(f"SELECT count(*) n FROM {FQ}.jurisdiction_requirements_cited").n)
    add("§2e", "  verification_status split",
        lambda: ", ".join(f"{r.s}={r.n}" for r in spark.sql(
            f"SELECT coalesce(verification_status,'NULL') s, count(*) n FROM {FQ}.jurisdiction_requirements_cited GROUP BY 1 ORDER BY 2 DESC").collect()))
    add("§2e", "  scrap-metal rows by status",
        lambda: ", ".join(f"{r.s}={r.n}" for r in spark.sql(
            f"SELECT coalesce(verification_status,'NULL') s, count(*) n FROM {FQ}.jurisdiction_requirements_cited "
            f"WHERE requirement_type LIKE 'scrap%' GROUP BY 1 ORDER BY 2 DESC").collect()) or "0")

    # §5b-2: field-cost evidence
    add("§5b-2", "field_cost_benchmark_register status split",
        lambda: ", ".join(f"{r.s}={r.n}" for r in spark.sql(
            f"SELECT coalesce(verification_status,'NULL') s, count(*) n FROM {FQ}.field_cost_benchmark_register GROUP BY 1 ORDER BY 2 DESC").collect()))
    add("§5b-2", "bottom_up_reference total cost_base_usd",
        lambda: "${:,.0f}".format(one(
            f"SELECT coalesce(sum(cost_base_usd),0) v FROM {FQ}.v_sow_demo_wave_cost_rollup WHERE scenario='bottom_up_reference'").v))
    add("§5b-2", "  bottom_up_reference by evidence_tier",
        lambda: ", ".join(f"{r.t}={r.n} rows/${r.v:,.0f}" for r in spark.sql(
            f"SELECT evidence_tier t, count(*) n, coalesce(sum(cost_base_usd),0) v FROM {FQ}.v_sow_demo_wave_cost_rollup "
            f"WHERE scenario='bottom_up_reference' GROUP BY 1 ORDER BY 3 DESC").collect()))
    add("§5b-2", "roi_calculator_assumptions field_cost populated / NULL base",
        lambda: (lambda r: f"{r.pop} / {r.nul}")(one(
            f"SELECT count(*) FILTER (WHERE base_value IS NOT NULL) pop, count(*) FILTER (WHERE base_value IS NULL) nul "
            f"FROM {FQ}.roi_calculator_assumptions WHERE param_group='field_cost'")))

    # Release gates: SP grants + live app count
    def _grants():
        rows = spark.sql(f"SHOW GRANTS `{APP_SP_ID}` ON SCHEMA {FQ}").collect()
        return f"{len(rows)} rows" + (": " + ", ".join(sorted({r[1] for r in rows})) if rows else "")
    add("gate", f"SHOW GRANTS rows for app SP {APP_SP_ID[:8]} on {FQ}", _grants)

    def _apps():
        active = []
        for name in PROJECT_APPS:
            try:
                a = w.apps.get(name)
                if a.compute_status and str(a.compute_status.state).split(".")[-1] == "ACTIVE":
                    active.append(name)
            except Exception:
                pass  # deleted / not deployed in this workspace
        return f"{len(active)} (target 2): {', '.join(active) or 'none'}"
    add("gate", "project apps with compute ACTIVE", _apps)
    return out


def check_release_numbers(w: WorkspaceClient) -> Status:
    _banner("10/10  RELEASE NUMBERS (paste into PARTNER-PLAYBOOK)")
    rows = release_numbers(w)
    print("\n| Section | Metric | Value |\n| --- | --- | --- |")
    for sec, metric, val in rows:
        print(f"| {sec} | {metric.strip()} | {val} |")
    print()
    errors = [m for _, m, v in rows if isinstance(v, str) and v.startswith("ERROR")]
    if errors:
        _row("Release numbers", Status.YELLOW, f"{len(errors)} queries errored")
        return Status.YELLOW
    _row("Release numbers", Status.GREEN, f"{len(rows)} figures generated")
    return Status.GREEN


# ===================================================================
# MAIN
# ===================================================================
def run_healthcheck():
    print("\n" + "#" * 60)
    print("#  COPPER RETIREMENT — PRE-DEMO HEALTH CHECK")
    print(f"#  Timestamp: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("#" * 60)

    w = WorkspaceClient()
    results = {}
    results["Apps"] = check_apps(w)
    results["Endpoints"] = check_endpoints(w)
    results["Pipelines"] = check_pipelines(w)
    results["Lakebase"] = check_lakebase(w)
    results["VectorSearch"] = check_vector_search(w)
    results["MV_Freshness"] = check_mv_freshness(w)
    results["InferenceTable"] = check_inference_table(w)
    results["LakebaseSync"] = check_lakebase_sync(w)
    results["CitationInvariant"] = check_citation_invariant(w)
    results["ReleaseNumbers"] = check_release_numbers(w)

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    overall = Status.GREEN
    for component, status in results.items():
        _row(component, status)
        if status == Status.RED:
            overall = Status.RED
        elif status == Status.YELLOW and overall != Status.RED:
            overall = Status.YELLOW

    print(f"\n  {'='*56}")
    overall_label = {Status.GREEN: "ALL CLEAR — Demo ready!",
                     Status.YELLOW: "WARNINGS — Review yellow items",
                     Status.RED: "ISSUES FOUND — Fix red items before demo"}
    print(f"  OVERALL: [{overall.value}]  {overall_label[overall]}")
    print(f"  {'='*56}\n")
    return overall


if __name__ == "__main__":
    run_healthcheck()
else:
    # When %run'd from a notebook
    run_healthcheck()
