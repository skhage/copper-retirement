# Copper Retirement Schema — Overview

## Business Context

The **Lakelink Fiber Copper Retirement** program manages the systematic replacement of legacy copper telecommunications infrastructure with modern fiber optic technology across 6 legacy states (CO, MN, WA, OR, ID, AZ). This schema (`cdm_tmforum.copper_retirement`) contains all operational, analytical, and ML data supporting the retirement program.

## Schema Statistics

* **44 user-facing tables** across 7 data domains
* **3 Metric Views**: project status KPIs, customer impact, EBITDA impact
* **8 Materialized Views**: DLP bronze/silver/gold layers
* **2 Vector Search indexes**: regulatory document RAG
* **1 ML model** (V5 risk scoring): served via `copper-retirement-risk` endpoint

## Data Domains

| Domain | Tables | Description |
|--------|--------|-------------|
| **Physical Plant** | 6 | Physical copper infrastructure — devices, cable pairs, wire center boundaries |
| **Circuits & Services** | 6 | Customer-facing services, device-to-service impact, revenue at risk |
| **Customer Impact** | 4 | Customer impact metrics and feature engineering |
| **Risk & ML** | 9 | ML training targets, predictions, fairness reports, features |
| **Regulatory** | 8 | FCC broadband data, regulatory documents, vector search, PUC requirements |
| **Financial & EBITDA** | 5 | Commodity pricing, cost forecasting, EBITDA impact |
| **Operations** | 6 | Dig-safe incidents, contractor performance, wire center scorecards |

## Medallion Architecture

This schema follows a **bronze → silver → gold** medallion pattern implemented via a Lakeflow Spark Declarative Pipeline:

* **Bronze**: Raw filtered data from TMF CDM source tables (`bronze_copper_devices`, `bronze_copper_services`, `bronze_dig_safe_incidents`)
* **Silver**: Enriched and joined data (`silver_copper_plant_enriched`, `silver_device_service_impact`, `silver_contract_constraints`, `silver_resource_capacity`, `silver_revenue_recognition_constraints`)
* **Gold**: Business-ready aggregations (`gold_retirement_executive_summary`, `gold_wire_center_scorecard`, `gold_contractor_scorecard`, `gold_circuit_revenue_at_risk`, `gold_device_risk_predictions`)

## Key Metric Views

* **`copper_retirement_project_status`** — Top-level KPIs: device counts, retirement progress, risk distribution
* **`copper_customers_impacted`** — Customer counts and service disruption tracking
* **`copper_ebitda_impact_achieved`** — Financial impact: annual savings, avoided maintenance, revenue retention

## Legacy States

All data is scoped to 6 legacy copper states: **CO, MN, WA, OR, ID, AZ**. These are the states where Lakelink Fiber is actively retiring copper plant. Non-legacy states (CA, TX, FL, NY, OH, IL) are excluded.

## Source Catalog

Parent data originates from the TMF CDM catalog `cdm_tmforum` across schemas: `tmf_enterprise`, `tmf_customer`, `tmf_shared_geography`, `tmf_service`, `tmf_resource`.

## Dashboards

* **Lakelink Fiber — Revenue Assurance Command Center** — Executive revenue assurance dashboard

## Applications

* **copper-map** — Geographic visualization of copper plant and retirement progress
* **regulatory-assistant** — RAG-powered regulatory Q&A chatbot
* **dig-triage** — Dig-safe incident triage and contractor assignment
* **retirement-plan** — Wire center retirement planning tool
* **commodity-dashboard** — Copper/fiber commodity price tracking
