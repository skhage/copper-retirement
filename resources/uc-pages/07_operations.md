# Operations Domain

**Schema:** `cdm_tmforum.copper_retirement`

## Overview

Dig-safe incidents, contractor performance, wire center scorecards, and project status KPIs.

## Tables (6)

| Table | Type | Description |
|-------|------|-------------|
| `dig_safe_incident` | MANAGED | Source table for dig-safe excavation incidents with damage severity |
| `bronze_dig_safe_incidents` | MATERIALIZED_VIEW | Bronze layer: dig-safe incident registry with contractor enrichment |
| `contractor_performance` | MANAGED | Contractor performance baseline data -- safety scores, project history, operational metrics |
| `gold_contractor_scorecard` | MATERIALIZED_VIEW | Gold layer: contractor scorecard with actual incident and work order metrics |
| `gold_wire_center_scorecard` | MATERIALIZED_VIEW | Gold layer: per-wire-center retirement readiness scorecard |
| `copper_retirement_project_status` | METRIC_VIEW | Copper retirement project status KPIs |

## Key Relationships

* contractor_id links contractor_performance -> gold_contractor_scorecard
* wire_center_clli links gold_wire_center_scorecard -> wire_center_boundary
* copper_retirement_project_status is a METRIC VIEW for top-level KPIs

## Operational Workflows

### Dig-Safe Triage
1. `dig_safe_incident` captures raw excavation incident reports
2. `bronze_dig_safe_incidents` enriches incidents with contractor info
3. `gold_contractor_scorecard` aggregates contractor safety and performance
4. The `dig-triage` app uses this data for incident assignment and tracking

### Wire Center Readiness
1. `gold_wire_center_scorecard` combines device counts, risk tiers, customer impact, and regulatory readiness per wire center
2. Used by `retirement-plan` app for prioritization
3. Feeds the `copper-map` geographic visualization

## Table Details

### `dig_safe_incident` (Managed)

> Source table for dig-safe excavation incidents. Each row = one incident with damage assessment.

Key columns: incident_id, incident_date, location_latitude, location_longitude, contractor_id, damage_severity, damage_type, utility_type, state_code, wire_center_clli, root_cause

### `bronze_dig_safe_incidents` (Materialized View)

> Bronze layer: dig-safe incident registry with contractor enrichment.

Key columns: incident_id, incident_date, contractor_id, contractor_name, safety_score, damage_severity, state_code, h3_index

### `contractor_performance` (Managed)

> Contractor performance baseline data -- safety scores, project history, and operational metrics.

Key columns: contractor_id, contractor_name, safety_score, total_projects, incidents_count, avg_completion_days, certification_status, states_served

### `gold_contractor_scorecard` (Materialized View)

> Gold layer: contractor scorecard with actual incident and work order metrics.

Key columns: contractor_id, contractor_name, total_incidents, severity_distribution, avg_response_time, safety_trend, recommendation_score

### `gold_wire_center_scorecard` (Materialized View)

> Gold layer: per-wire-center retirement readiness scorecard.

Key columns: wire_center_clli, wire_center_name, state_code, total_devices, devices_retired, pct_retired, customers_impacted, risk_score, readiness_tier, regulatory_compliant

### `copper_retirement_project_status` (Metric View)

> Copper retirement project status KPIs -- tracks device inventory, retirement progress, risk distribution.

This is a governed metric view providing top-level program KPIs. Key dimensions: state_code. Key measures: total_devices, devices_retired, pct_complete, high_risk_count, customers_impacted, estimated_completion_date.
