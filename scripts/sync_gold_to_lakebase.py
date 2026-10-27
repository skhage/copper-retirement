# Databricks notebook source
"""Sync gold/silver tables from Unity Catalog to the Lakebase copper_app schema (ACC-CREATE-LAKEBASE-SYNC-SCRIPT).

Used by bundle/resources/lakebase_sync.job.yml (notebook_task, base_parameters catalog / schema / lakebase_project).
It can also run as a plain script:
  python sync_gold_to_lakebase.py --catalog <catalog> --schema <schema> --lakebase-project <project> [--tables a,b] [--dry-run]

Semantics: an idempotent, NON-DESTRUCTIVE keyed upsert.
  * Only the columns that exist in BOTH the UC source and the Lakebase target are written.
    App-owned write-back columns (for example dig_incidents.triage_status and assigned_crew_id) are never
    in the source, so they are preserved.
  * UPDATE runs only on rows whose values changed (IS DISTINCT FROM). INSERT runs only for new keys.
    updated_at / synced_at are set to NOW() on updated rows.
  * Rows that exist only in the target are kept and reported as target_only_rows_kept. Nothing is deleted.
  * Duplicate source keys abort that table's transaction, and nothing is written for it.
  * The Lakebase host is resolved from the endpoint, so no host is hardcoded. Catalog, schema and project are parameters.
Requires: psycopg[binary], databricks-sdk>=0.118.0.
Reference run 2026-10-27 (cdm_tmforum.copper_retirement -> copper-task-board): 10/10 tables OK, and a re-run made 0 changes.
"""
import re
import time

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# target (copper_app) -> (UC source, key columns, {target_col: source_col} renames[, excluded target cols])
SYNC_SPECS = {
    "wire_center_scorecard":           ("gold_wire_center_scorecard",        ["wire_center_id"], {}),
    "executive_summary":               ("gold_retirement_executive_summary", ["state_code"], {}),
    "contractor_scorecard":            ("gold_contractor_scorecard",         ["contractor_performance_id"], {}),
    "dig_incidents":                   ("silver_dig_incident_enriched",      ["incident_id"],
                                        {"latitude": "incident_latitude", "longitude": "incident_longitude"},
                                        ["triage_priority"]),  # LB column is INTEGER, UC is 'P1'..'P4' text
    "retirement_milestones":           ("retirement_milestones",             ["milestone_id"], {}),
    "jurisdiction_requirements_cited": ("jurisdiction_requirements_cited",   ["requirement_key"], {}),
    "gold_wave_schedule":              ("gold_wave_schedule",                ["wire_center_id"], {}),
    "gold_copper_recovery_schedule":   ("gold_copper_recovery_schedule",     ["wire_center_id"], {}),
    "gold_contractor_assignment_plan": ("gold_contractor_assignment_plan",   ["wave", "contractor_id"], {}),
    "gold_reroute_options":            ("gold_reroute_options",              ["physical_device_id", "reroute_option_rank"], {}),
}
TOUCH_COLS = ("updated_at", "synced_at")


def _q(name):
    if not IDENT.match(name):
        raise ValueError(f"unsafe identifier: {name!r}")
    return '"' + name + '"'


def lakebase_connect(project, branch="production", endpoint="primary", dbname="databricks_postgres"):
    import psycopg
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    ep_name = f"projects/{project}/branches/{branch}/endpoints/{endpoint}"
    host = w.postgres.get_endpoint(name=ep_name).status.hosts.host
    tok = w.postgres.generate_database_credential(endpoint=ep_name).token
    return psycopg.connect(host=host, dbname=dbname, user=w.current_user.me().user_name,
                           password=tok, sslmode="require")


def sync_table(spark, conn, catalog, schema, target, source, keys, renames, exclude=(), pg_schema="copper_app", dry_run=False):
    for n in [catalog, schema, target, source, pg_schema, *keys]:
        _q(n)
    with conn.cursor() as cur:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position",
                    (pg_schema, target))
        tcols = [r[0] for r in cur.fetchall()]
    if not tcols:
        return {"target": target, "status": "SKIPPED_TARGET_MISSING"}
    sdf = spark.table(f"`{catalog}`.`{schema}`.`{source}`")
    scols = set(sdf.columns)
    pairs = [(t, renames.get(t, t)) for t in tcols if t not in exclude and renames.get(t, t) in scols]
    cols = [t for t, _ in pairs]
    missing_keys = [k for k in keys if k not in cols]
    if missing_keys:
        return {"target": target, "status": f"SKIPPED_KEY_MISSING {missing_keys}"}
    rows = sdf.selectExpr(*[f"`{s}` AS `{t}`" for t, s in pairs]).collect()
    nonkey = [c for c in cols if c not in keys]
    touch = [c for c in TOUCH_COLS if c in tcols and c not in cols]
    tq = f"{_q(pg_schema)}.{_q(target)}"
    on = " AND ".join(f"t.{_q(k)} = s.{_q(k)}" for k in keys)
    res = {"target": target, "source": f"{catalog}.{schema}.{source}", "source_rows": len(rows), "cols": len(cols)}
    with conn.cursor() as cur:
        cur.execute(f"CREATE TEMP TABLE _stg ON COMMIT DROP AS SELECT {', '.join(_q(c) for c in cols)} FROM {tq} WITH NO DATA")
        with cur.copy(f"COPY _stg ({', '.join(_q(c) for c in cols)}) FROM STDIN") as cp:
            for r in rows:
                cp.write_row(tuple(r))
        cur.execute(f"SELECT COUNT(*) FROM (SELECT {', '.join(_q(k) for k in keys)} FROM _stg GROUP BY {', '.join(_q(k) for k in keys)} HAVING COUNT(*) > 1) d")
        dups = cur.fetchone()[0]
        if dups:
            conn.rollback()
            return {**res, "status": f"FAILED_DUPLICATE_KEYS {dups}"}
        set_sql = ", ".join([f"{_q(c)} = s.{_q(c)}" for c in nonkey] + [f"{_q(c)} = NOW()" for c in touch])
        diff = (f" AND ({', '.join('t.' + _q(c) for c in nonkey)}) IS DISTINCT FROM ({', '.join('s.' + _q(c) for c in nonkey)})"
                if len(nonkey) > 1 else (f" AND t.{_q(nonkey[0])} IS DISTINCT FROM s.{_q(nonkey[0])}" if nonkey else ""))
        upd = 0
        if set_sql:
            cur.execute(f"UPDATE {tq} t SET {set_sql} FROM _stg s WHERE {on}{diff}")
            upd = cur.rowcount
        cur.execute(f"INSERT INTO {tq} ({', '.join(_q(c) for c in cols)}) SELECT {', '.join('s.' + _q(c) for c in cols)} FROM _stg s "
                    f"WHERE NOT EXISTS (SELECT 1 FROM {tq} t WHERE {on})")
        ins = cur.rowcount
        cur.execute(f"SELECT COUNT(*) FROM {tq} t WHERE NOT EXISTS (SELECT 1 FROM _stg s WHERE {on})")
        orphans = cur.fetchone()[0]
        if dry_run:
            conn.rollback()
        else:
            conn.commit()
    return {**res, "updated": upd, "inserted": ins, "target_only_rows_kept": orphans,
            "status": "DRY_RUN" if dry_run else "OK"}


def run_sync(spark, catalog, schema, lakebase_project, tables=None, dry_run=False):
    conn = lakebase_connect(lakebase_project)
    out = []
    try:
        for target, spec in SYNC_SPECS.items():
            source, keys, renames = spec[:3]
            exclude = spec[3] if len(spec) > 3 else []
            if tables and target not in tables:
                continue
            t0 = time.time()
            try:
                r = sync_table(spark, conn, catalog, schema, target, source, keys, renames, exclude=exclude, dry_run=dry_run)
            except Exception as e:
                conn.rollback()
                r = {"target": target, "status": f"ERROR {type(e).__name__}: {str(e)[:300]}"}
            r["secs"] = round(time.time() - t0, 1)
            print(r)
            out.append(r)
    finally:
        conn.close()
    return out


def _params():
    """Read job parameters from notebook widgets (notebook_task) or from argparse (plain script)."""
    try:
        dbutils  # noqa: F821  (defined in Databricks notebooks)
        for k, d in [("catalog", ""), ("schema", "copper_retirement"), ("lakebase_project", "copper-task-board"),
                     ("tables", ""), ("dry_run", "false")]:
            dbutils.widgets.text(k, d)  # noqa: F821
        g = dbutils.widgets.get  # noqa: F821
        return g("catalog"), g("schema"), g("lakebase_project"), g("tables"), g("dry_run").lower() == "true"
    except NameError:
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument("--catalog", required=True)
        p.add_argument("--schema", default="copper_retirement")
        p.add_argument("--lakebase-project", default="copper-task-board")
        p.add_argument("--tables", default="")
        p.add_argument("--dry-run", action="store_true")
        a = p.parse_args()
        return a.catalog, a.schema, a.lakebase_project, a.tables, a.dry_run


if __name__ == "__main__":
    catalog, schema, project, tables, dry_run = _params()
    if not catalog:
        raise ValueError("catalog parameter is required")
    try:
        spark  # noqa: F821
    except NameError:
        from databricks.connect import DatabricksSession
        spark = DatabricksSession.builder.getOrCreate()
    results = run_sync(spark, catalog, schema, project,
                       tables=[t.strip() for t in tables.split(",") if t.strip()] or None, dry_run=dry_run)
    bad = [r for r in results if not str(r.get("status", "")).startswith(("OK", "DRY_RUN"))]
    print(f"SYNC SUMMARY: {len(results) - len(bad)}/{len(results)} tables OK")
    if bad:
        raise RuntimeError(f"Lakebase sync failures: {bad}")
