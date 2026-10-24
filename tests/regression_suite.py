"""Copper Retirement — Regression Test Suite

Repeatable validation checks for the copper retirement demo:
  1. Golden queries for 5 metric views (±10% tolerance)
  2. App health checks (HTTP 200 + deployment SUCCEEDED)
  3. Endpoint canary (latency < 500ms, non-null predictions)
  4. Semantic completeness (table/column COMMENT coverage > 95%)

Usage:
  - Run as a Databricks notebook cell: %run ./tests/regression_suite
  - Or import and call: from tests.regression_suite import run_all
  - Or via pytest: pytest tests/regression_suite.py -v

Baseline snapshot: 2026-09-21
Author: @qa (automated)
"""
import os
import sys
import time
import json
import traceback
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Parameterized (ACC-DE-PARAMETERIZE): defaults match bundle variables catalog_name/schema_name
CATALOG = os.environ.get("COPPER_CATALOG", "cdm_tmforum")
SCHEMA = os.environ.get("COPPER_SCHEMA", "copper_retirement")
TOLERANCE = 0.10  # ±10%

# Legacy states for the copper retirement project
LEGACY_STATES = {"CO", "MN", "WA", "OR", "ID", "AZ"}

# 5 primary demo apps (deployment + compute checks)
DEMO_APPS = [
    "commodity-dashboard",
    "copper-map",
    "dig-triage",
    "regulatory-assistant",
    "retirement-plan",
]

# Serving endpoint
SERVING_ENDPOINT = "copper-retirement-risk"
ENDPOINT_LATENCY_THRESHOLD_MS = 500

# Semantic completeness thresholds
TABLE_COMMENT_THRESHOLD = 0.95
COLUMN_COMMENT_THRESHOLD = 0.95


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------
@dataclass
class CheckResult:
    name: str
    passed: bool
    severity: str = "INFO"  # BLOCKER | WARNING | INFO
    detail: str = ""
    value: Optional[float] = None
    expected: Optional[float] = None


def _within_tolerance(actual, expected, tol=TOLERANCE):
    """Return True if actual is within ±tol of expected."""
    if expected == 0:
        return actual == 0
    return abs(actual - expected) / abs(expected) <= tol


# ---------------------------------------------------------------------------
# 1. Golden Metric View Queries
# ---------------------------------------------------------------------------
# Baselines captured 2026-09-21 from live metric views.
# Each entry: (metric_view, measure_col, baseline_value)
GOLDEN_QUERIES = [
    # copper_retirement_project_status
    ("copper_retirement_project_status", "Total Copper Devices", 2672),
    ("copper_retirement_project_status", "Active Devices", 1825),
    ("copper_retirement_project_status", "Critical Risk Devices", 383),
    # copper_customers_impacted
    ("copper_customers_impacted", "Customers Impacted", 288),
    ("copper_customers_impacted", "Services at Risk", 304),
    ("copper_customers_impacted", "Voice Services at Risk", 141),
    ("copper_customers_impacted", "Broadband Services at Risk", 61),
    # copper_ebitda_impact_achieved
    ("copper_ebitda_impact_achieved", "Total Annual Revenue at Risk", 603845712.24),
    ("copper_ebitda_impact_achieved", "Total Circuits", 14777),
    ("copper_ebitda_impact_achieved", "Avg Revenue per Circuit", 40863.89),
    # copper_ebitda_impact_forecast
    ("copper_ebitda_impact_forecast", "Forecast Revenue at Risk", 452884286.40),
    ("copper_ebitda_impact_forecast", "Forecast EBITDA Impact", 96567652.41),
    ("copper_ebitda_impact_forecast", "Circuit Count", 111900),
    # copper_commodity_sell_hold_signal
    ("copper_commodity_sell_hold_signal", "Actual LME Price USD per Ton", 8723.55),
    ("copper_commodity_sell_hold_signal", "Actual COMEX Price USD per Lb", 3.9569),
    ("copper_commodity_sell_hold_signal", "Trading Days Count", 1747),
]


def run_golden_queries(spark) -> list[CheckResult]:
    """Execute golden queries against the 5 metric views."""
    results = []
    for mv_name, measure_col, baseline in GOLDEN_QUERIES:
        fqn = f"{CATALOG}.{SCHEMA}.{mv_name}"
        check_name = f"golden/{mv_name}/{measure_col}"
        try:
            row = spark.sql(
                f"SELECT MEASURE(`{measure_col}`) AS val FROM {fqn}"
            ).collect()[0]
            actual = float(row.val) if row.val is not None else None
            if actual is None:
                results.append(CheckResult(
                    name=check_name, passed=False, severity="BLOCKER",
                    detail=f"NULL result from MEASURE(`{measure_col}`)",
                    value=actual, expected=baseline,
                ))
            elif _within_tolerance(actual, baseline):
                results.append(CheckResult(
                    name=check_name, passed=True, severity="INFO",
                    detail=f"actual={actual:.4f}, baseline={baseline:.4f}, within ±{TOLERANCE*100:.0f}%",
                    value=actual, expected=baseline,
                ))
            else:
                drift_pct = abs(actual - baseline) / abs(baseline) * 100 if baseline else float("inf")
                results.append(CheckResult(
                    name=check_name, passed=False, severity="BLOCKER",
                    detail=f"DRIFT {drift_pct:.1f}%: actual={actual:.4f}, baseline={baseline:.4f}",
                    value=actual, expected=baseline,
                ))
        except Exception as e:
            results.append(CheckResult(
                name=check_name, passed=False, severity="BLOCKER",
                detail=f"QUERY ERROR: {str(e)[:300]}",
            ))
    return results


# ---------------------------------------------------------------------------
# 2. App Health Checks
# ---------------------------------------------------------------------------
def run_app_health_checks(w) -> list[CheckResult]:
    """Check that demo apps are deployed and compute is active."""
    results = []
    try:
        all_apps = {a.name: a for a in w.apps.list()}
    except Exception as e:
        results.append(CheckResult(
            name="apps/list", passed=False, severity="BLOCKER",
            detail=f"Cannot list apps: {e}",
        ))
        return results

    for app_name in DEMO_APPS:
        check_name = f"app/{app_name}"
        app = all_apps.get(app_name)
        if app is None:
            results.append(CheckResult(
                name=check_name, passed=False, severity="BLOCKER",
                detail=f"App '{app_name}' not found in workspace",
            ))
            continue

        # Check deployment status
        deploy_ok = False
        deploy_state = "unknown"
        if app.active_deployment and hasattr(app.active_deployment, "status"):
            deploy_state = app.active_deployment.status.state.value
            deploy_ok = deploy_state == "SUCCEEDED"

        # Check compute status
        compute_ok = False
        compute_state = "unknown"
        if hasattr(app, "compute_status") and app.compute_status:
            compute_state = app.compute_status.state.value
            compute_ok = compute_state == "ACTIVE"

        passed = deploy_ok and compute_ok
        severity = "BLOCKER" if not deploy_ok else ("WARNING" if not compute_ok else "INFO")
        results.append(CheckResult(
            name=check_name, passed=passed, severity=severity,
            detail=f"deploy={deploy_state}, compute={compute_state}",
        ))

        # HTTP health probe (best-effort; app URL may not be reachable from serverless)
        if hasattr(app, "url") and app.url:
            try:
                import requests as _req
                resp = _req.get(app.url, timeout=10, allow_redirects=True)
                http_ok = resp.status_code == 200
                results.append(CheckResult(
                    name=f"app/{app_name}/http",
                    passed=http_ok,
                    severity="WARNING" if not http_ok else "INFO",
                    detail=f"HTTP {resp.status_code} from {app.url}",
                ))
            except Exception as e:
                results.append(CheckResult(
                    name=f"app/{app_name}/http",
                    passed=False, severity="WARNING",
                    detail=f"HTTP probe failed (may be expected from serverless): {str(e)[:150]}",
                ))
    return results


# ---------------------------------------------------------------------------
# 3. Endpoint Canary
# ---------------------------------------------------------------------------
# Representative feature vector for the V5 risk model
CANARY_PAYLOAD = {
    "alarm_count": 2.0,
    "critical_alarm_rate": 0.089,
    "service_affecting_rate": 0.092,
    "sla_breach_count": 1.0,
    "sla_breach_rate": 0.073,
    "test_fail_rate": 0.073,
    "problem_count": 1.0,
    "recurring_problem_rate": 0.0,
    "alarm_count_prank": 0.0015,
    "critical_alarm_prank": 0.469,
    "svc_affecting_prank": 0.437,
    "sla_breach_prank": 0.446,
    "test_fail_prank": 0.450,
    "problem_count_prank": 0.004,
    "recurring_prob_prank": 0.022,
    # V5 model additional features (39-feature set)
    "dispute_count": 0.0,
    "escalated_dispute_count": 0.0,
    "sla_breach_dispute_count": 0.0,
    "months_since_last_dispute": 12.0,
    "complaint_count": 1.0,
    "complaint_rate_per_month": 0.08,
    "escalated_complaint_count": 0.0,
    "high_severity_complaint_count": 0.0,
    "has_active_contract": 1.0,
    "contract_expiry_days_remaining": 180.0,
    "total_contracts": 1.0,
    "active_contract_count": 1.0,
    "linked_customer_count": 1.0,
    "migration_blocked_by_contract": 0.0,
    "firmware_age_days": 1200.0,
    "firmware_is_obsolete": 1.0,
    "firmware_generations_behind": 3.0,
    "avg_monthly_usage": 450.0,
    "peak_utilization_pct": 0.72,
    "usage_trend": -0.02,
    "months_active": 48.0,
    "capacity_headroom_pct": 0.28,
    "is_over_utilized": 0.0,
    "composite_risk_score": 0.65,
}


def run_endpoint_canary(w) -> list[CheckResult]:
    """Check serving endpoint is READY, responds with low latency, and returns non-null predictions."""
    results = []

    # 3a. Endpoint state
    try:
        ep = w.serving_endpoints.get(SERVING_ENDPOINT)
        ready = ep.state.ready.value == "READY"
        results.append(CheckResult(
            name="endpoint/state",
            passed=ready,
            severity="BLOCKER" if not ready else "INFO",
            detail=f"state={ep.state.ready.value}",
        ))
    except Exception as e:
        results.append(CheckResult(
            name="endpoint/state", passed=False, severity="BLOCKER",
            detail=f"Cannot get endpoint: {e}",
        ))
        return results

    # 3b. Latency + non-null prediction
    try:
        import requests as _req
        workspace_url = w.config.host.rstrip("/")
        # Get auth token — try multiple sources for compatibility
        token = None
        # 1. Try SDK config token
        try:
            token = w.config.token
        except Exception:
            pass
        # 2. Try notebook context API token
        if not token:
            try:
                token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
            except Exception:
                pass
        # 3. Try environment variable
        if not token:
            token = os.environ.get("DATABRICKS_TOKEN", "")
        if not token:
            results.append(CheckResult(
                name="endpoint/auth", passed=False, severity="WARNING",
                detail="No auth token available for endpoint canary — skipping invocation test",
            ))
            return results

        start = time.time()
        resp = _req.post(
            f"{workspace_url}/serving-endpoints/{SERVING_ENDPOINT}/invocations",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"dataframe_records": [CANARY_PAYLOAD]},
            timeout=10,
        )
        latency_ms = (time.time() - start) * 1000

        latency_ok = latency_ms < ENDPOINT_LATENCY_THRESHOLD_MS
        results.append(CheckResult(
            name="endpoint/latency",
            passed=latency_ok,
            severity="WARNING" if not latency_ok else "INFO",
            detail=f"{latency_ms:.0f}ms (threshold: {ENDPOINT_LATENCY_THRESHOLD_MS}ms)",
            value=latency_ms,
            expected=float(ENDPOINT_LATENCY_THRESHOLD_MS),
        ))

        if resp.status_code == 200:
            body = resp.json()
            predictions = body.get("predictions", body.get("dataframe_records", []))
            has_prediction = len(predictions) > 0 if isinstance(predictions, list) else predictions is not None
            results.append(CheckResult(
                name="endpoint/prediction",
                passed=has_prediction,
                severity="BLOCKER" if not has_prediction else "INFO",
                detail=f"response_keys={list(body.keys())}, has_prediction={has_prediction}",
            ))
        else:
            results.append(CheckResult(
                name="endpoint/prediction",
                passed=False, severity="WARNING",
                detail=f"HTTP {resp.status_code}: {resp.text[:200]}",
            ))
    except Exception as e:
        results.append(CheckResult(
            name="endpoint/invocation", passed=False, severity="WARNING",
            detail=f"Canary invocation failed: {str(e)[:200]}",
        ))
    return results


# ---------------------------------------------------------------------------
# 4. Semantic Completeness
# ---------------------------------------------------------------------------
def run_semantic_completeness(spark) -> list[CheckResult]:
    """Check table and column COMMENT coverage in copper_retirement schema."""
    results = []

    # 4a. Table-level comments (exclude internal/materialization tables)
    table_df = spark.sql(f"""
        SELECT table_name, comment
        FROM {CATALOG}.information_schema.tables
        WHERE table_schema = '{SCHEMA}'
    """).toPandas()
    user_tables = table_df[
        ~table_df["table_name"].str.startswith("__")
        & ~table_df["table_name"].str.startswith("event_log_")
    ]
    total_t = len(user_tables)
    with_t = int(user_tables["comment"].notna().sum())
    pct_t = with_t / total_t if total_t > 0 else 0.0
    passed_t = pct_t >= TABLE_COMMENT_THRESHOLD
    results.append(CheckResult(
        name="semantic/table_comments",
        passed=passed_t,
        severity="WARNING" if not passed_t else "INFO",
        detail=f"{with_t}/{total_t} tables ({pct_t*100:.1f}%, threshold {TABLE_COMMENT_THRESHOLD*100:.0f}%)",
        value=pct_t, expected=TABLE_COMMENT_THRESHOLD,
    ))

    # 4b. Column-level comments
    col_df = spark.sql(f"""
        SELECT table_name, column_name, comment
        FROM {CATALOG}.information_schema.columns
        WHERE table_schema = '{SCHEMA}'
    """).toPandas()
    user_cols = col_df[
        ~col_df["table_name"].str.startswith("__")
        & ~col_df["table_name"].str.startswith("event_log_")
    ]
    total_c = len(user_cols)
    with_c = int(user_cols["comment"].notna().sum())
    pct_c = with_c / total_c if total_c > 0 else 0.0
    passed_c = pct_c >= COLUMN_COMMENT_THRESHOLD
    results.append(CheckResult(
        name="semantic/column_comments",
        passed=passed_c,
        severity="WARNING" if not passed_c else "INFO",
        detail=f"{with_c}/{total_c} columns ({pct_c*100:.1f}%, threshold {COLUMN_COMMENT_THRESHOLD*100:.0f}%)",
        value=pct_c, expected=COLUMN_COMMENT_THRESHOLD,
    ))

    # 4c. List tables missing comments (if any)
    missing = user_tables[user_tables["comment"].isna()]["table_name"].tolist()
    if missing:
        results.append(CheckResult(
            name="semantic/tables_missing_comments",
            passed=False, severity="INFO",
            detail=f"Tables without comments: {missing[:20]}",
        ))

    return results


# ---------------------------------------------------------------------------
# 5. Data Integrity Spot Checks
# ---------------------------------------------------------------------------
def run_data_integrity_checks(spark) -> list[CheckResult]:
    """Spot-check critical data invariants."""
    results = []

    # 5a. Legacy states: copper devices should be in CO, MN, WA, OR, ID, AZ only
    try:
        states = spark.sql(f"""
            SELECT DISTINCT State
            FROM {CATALOG}.{SCHEMA}.copper_retirement_project_status
        """).toPandas()["State"].tolist()
        # Metric view returns all 50 states; legacy states should be a subset
        has_legacy = all(s in states for s in LEGACY_STATES)
        results.append(CheckResult(
            name="data/legacy_states_present",
            passed=has_legacy,
            severity="BLOCKER" if not has_legacy else "INFO",
            detail=f"Legacy states {LEGACY_STATES} present in data: {has_legacy}. Total states: {len(states)}",
        ))
    except Exception as e:
        results.append(CheckResult(
            name="data/legacy_states_present", passed=False, severity="WARNING",
            detail=f"Could not verify legacy states: {str(e)[:200]}",
        ))

    # 5b. Risk predictions non-empty
    try:
        cnt = spark.sql(f"""
            SELECT COUNT(*) as cnt FROM {CATALOG}.{SCHEMA}.gold_device_risk_predictions
        """).collect()[0].cnt
        ok = cnt > 0
        results.append(CheckResult(
            name="data/risk_predictions_populated",
            passed=ok,
            severity="BLOCKER" if not ok else "INFO",
            detail=f"gold_device_risk_predictions row count: {cnt}",
            value=float(cnt),
        ))
    except Exception as e:
        results.append(CheckResult(
            name="data/risk_predictions_populated", passed=False, severity="BLOCKER",
            detail=f"Cannot query risk predictions: {str(e)[:200]}",
        ))

    # 5c. DLP materialized views are populated
    mvs = [
        "bronze_copper_devices", "bronze_copper_services", "bronze_dig_safe_incidents",
        "silver_copper_plant_enriched", "silver_device_service_impact",
        "gold_contractor_scorecard", "gold_retirement_executive_summary",
        "gold_wire_center_scorecard",
    ]
    for mv in mvs:
        try:
            cnt = spark.sql(f"SELECT COUNT(*) as cnt FROM {CATALOG}.{SCHEMA}.{mv}").collect()[0].cnt
            ok = cnt > 0
            results.append(CheckResult(
                name=f"data/mv_populated/{mv}",
                passed=ok,
                severity="BLOCKER" if not ok else "INFO",
                detail=f"row count: {cnt}",
                value=float(cnt),
            ))
        except Exception as e:
            results.append(CheckResult(
                name=f"data/mv_populated/{mv}", passed=False, severity="BLOCKER",
                detail=f"Cannot query MV: {str(e)[:200]}",
            ))

    return results


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_all(spark=None, w=None) -> list[CheckResult]:
    """Execute the full regression suite. Returns a list of CheckResult.

    Args:
        spark: SparkSession (auto-detected from globals if not passed)
        w: WorkspaceClient (auto-created if not passed)
    """
    if spark is None:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
    if w is None:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()

    all_results: list[CheckResult] = []

    print("=" * 70)
    print("COPPER RETIREMENT — REGRESSION TEST SUITE")
    print(f"Run timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("=" * 70)

    sections = [
        ("1. Golden Metric View Queries", lambda: run_golden_queries(spark)),
        ("2. App Health Checks", lambda: run_app_health_checks(w)),
        ("3. Endpoint Canary", lambda: run_endpoint_canary(w)),
        ("4. Semantic Completeness", lambda: run_semantic_completeness(spark)),
        ("5. Data Integrity Spot Checks", lambda: run_data_integrity_checks(spark)),
    ]

    for section_name, fn in sections:
        print(f"\n--- {section_name} ---")
        try:
            section_results = fn()
            all_results.extend(section_results)
            for r in section_results:
                icon = "PASS" if r.passed else "FAIL"
                print(f"  [{icon}] {r.name}: {r.detail}")
        except Exception as e:
            print(f"  [ERROR] Section failed: {e}")
            traceback.print_exc()
            all_results.append(CheckResult(
                name=f"section/{section_name}",
                passed=False, severity="BLOCKER",
                detail=f"Unhandled error: {str(e)[:200]}",
            ))

    # Summary
    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed = total - passed
    blockers = sum(1 for r in all_results if not r.passed and r.severity == "BLOCKER")
    warnings = sum(1 for r in all_results if not r.passed and r.severity == "WARNING")

    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {passed}/{total} passed, {failed} failed ({blockers} BLOCKER, {warnings} WARNING)")
    verdict = "PASS" if blockers == 0 and warnings == 0 else ("PASS-WITH-NOTES" if blockers == 0 else "FAIL")
    print(f"VERDICT: {verdict}")
    print("=" * 70)

    return all_results


# ---------------------------------------------------------------------------
# pytest entry points
# ---------------------------------------------------------------------------
def _get_spark():
    from pyspark.sql import SparkSession
    return SparkSession.builder.getOrCreate()


def _get_w():
    from databricks.sdk import WorkspaceClient
    return WorkspaceClient()


def test_golden_queries():
    results = run_golden_queries(_get_spark())
    blockers = [r for r in results if not r.passed and r.severity == "BLOCKER"]
    assert not blockers, f"Golden query blockers: {[r.name + ': ' + r.detail for r in blockers]}"


def test_app_health():
    results = run_app_health_checks(_get_w())
    blockers = [r for r in results if not r.passed and r.severity == "BLOCKER"]
    assert not blockers, f"App health blockers: {[r.name + ': ' + r.detail for r in blockers]}"


def test_endpoint_canary():
    results = run_endpoint_canary(_get_w())
    blockers = [r for r in results if not r.passed and r.severity == "BLOCKER"]
    assert not blockers, f"Endpoint blockers: {[r.name + ': ' + r.detail for r in blockers]}"


def test_semantic_completeness():
    results = run_semantic_completeness(_get_spark())
    blockers = [r for r in results if not r.passed]
    assert not blockers, f"Semantic completeness issues: {[r.name + ': ' + r.detail for r in blockers]}"


def test_data_integrity():
    results = run_data_integrity_checks(_get_spark())
    blockers = [r for r in results if not r.passed and r.severity == "BLOCKER"]
    assert not blockers, f"Data integrity blockers: {[r.name + ': ' + r.detail for r in blockers]}"


# ---------------------------------------------------------------------------
# Direct execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_all()
