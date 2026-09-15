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

* bp_agreement_id links contractor_performance -> gold_contractor_scorecard
* wire_center_id / clli_code links gold_wire_center_scorecard -> wire_center_boundary
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

Key columns: incident_id, work_id, bp_agreement_id, geographic_address_id, network_route_id, state, latitude, longitude, incident_date, severity, cable_type, cable_damage_type, root_cause, contractor_at_fault, resolution_time_hours, repair_cost_amount. (24 cols, 5,000 rows)

### `bronze_dig_safe_incidents` (Materialized View)

> Bronze layer: dig-safe incident registry with contractor enrichment.

Key columns: incident_id, work_id, bp_agreement_id, incident_date, severity, contractor_name, contractor_type, contractor_safety_score, contractor_overall_rating, is_regulatory_violation, state. (30 cols, 5,000 rows)

### `contractor_performance` (Managed)

> Contractor performance baseline data -- safety scores, project history, and operational metrics.

Key columns: contractor_performance_id, bp_agreement_id, party_id, contractor_name, contractor_type, safety_score, osha_recordable_rate, incident_count, at_fault_incident_count, certification_status, sla_compliance_pct, geographic_coverage_states, primary_state, overall_rating. (27 cols, 10,000 rows)

### `gold_contractor_scorecard` (Materialized View)

> Gold layer: contractor scorecard with actual incident and work order metrics.

Key columns: contractor_performance_id, bp_agreement_id, party_id, contractor_name, safety_score, osha_recordable_rate, overall_rating, actual_incident_count, actual_at_fault_count, violation_count, total_incident_cost, avg_actual_resolution_hours, actual_sla_compliance_pct, dispatch_status. (36 cols, 10,000 rows)

### `gold_wire_center_scorecard` (Materialized View)

> Gold layer: per-wire-center retirement readiness scorecard.

Key columns: wire_center_id, wire_center_name, clli_code, state_code, fiber_ready, puc_filing_required, copper_device_count, critical_risk_devices, high_risk_devices, affected_service_count, affected_customer_count, retirement_readiness_score, retirement_priority_rank, annual_retire_priority. (34 cols, 103 rows)

### `copper_retirement_project_status` (Metric View)

> Copper retirement project status KPIs -- tracks device inventory, retirement progress, risk distribution.

This is a governed metric view providing top-level program KPIs. Key dimensions: State, Device Type, Risk Tier, Device Status, Fiber Ready, Wire Center, City. Key measures: Total Copper Devices, Active Devices, Faulty Devices, Critical Risk Devices, Fiber Ready Devices, Fiber Ready Pct, Critical Risk Pct, Avg Alarm Count, Total Problem Count, Avg SLA Breach Rate, Unique Wire Centers. (18 cols, 2,672 rows)
