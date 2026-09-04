# Technical Reference — Databricks Component Design

Deep technical reference for Claude Code to use while implementing the platform. Covers ingestion sources, geospatial design, Spark Declarative Pipelines, ML/MLOps, agents, Lakebase, and Apps.

## 1. Ingestion — Likely Sources & Method

| Source | What It Provides | Ingestion Method |
|---|---|---|
| FCC Broadband Data Collection (BDC) | Provider-reported technology-by-location broadband availability, semiannual filings; closest public proxy for "where is copper-based service today" [cite:16][cite:28] | Batch download of CSV extracts from FCC National Broadband Map "Data Downloads"; land as bronze via Auto Loader on cloud storage |
| FCC Broadband Serviceable Location Fabric | Canonical location dataset (addresses/points) used to key BDC records | Batch CSV/geodatabase load, same pattern as BDC |
| FCC Public Notices/Orders (copper retirement dockets) | Regulatory text for the compliance agent | Scheduled scrape/API pull of FCC ECFS/docket pages into a raw document store |
| State PUC filings/tariffs | State-level notice requirements and dockets | Per-state connector pattern (varies by state site); treat as incremental backlog |
| Lumen internal OSS/GIS/inventory exports (simulated in demo) | Actual copper plant location, cable counts, wire-center boundaries — the ground truth Lumen would supply in a real engagement | Simulate as CSV/GeoJSON files landed via Auto Loader; clearly label as synthetic in the demo |
| Commodity price feeds (LME copper API, commodity price APIs) | Historical and near-real-time copper pricing for forecasting [cite:33][cite:42] | REST API pull on a schedule (e.g., daily), landed via a Lakeflow job or Auto Loader on API dumps |
| Weather/soil data (NOAA, USGS) | Dig-risk features | Batch API pull |
| Contractor/vendor registries, state contractor licensing data | Workforce sourcing | Batch CSV pull / manual registry seed for demo |
| Network topology / circuit inventory (simulated) | Reroute recommendations for the triage agent | Simulated Delta table representing COs, fiber routes, circuit assignments |

Use **Lakeflow Connect** / **Auto Loader** for file-based cloud storage ingestion (the standard entry point for pipelines per Databricks docs) and a scheduled Lakeflow job wrapping REST calls for API sources (commodity prices, FCC data) [cite:20][cite:29].

## 2. Geospatial Design

- Use **H3 hexagonal indexing** as the common spatial key across all datasets — copper footprint proxy, jurisdiction boundaries, contractor coverage areas, and incident locations all get an `h3_cell` column at a consistent resolution (e.g., resolution 9–10 for neighborhood-level granularity) [cite:32][cite:38].
- The original Databricks Mosaic library popularized this H3-first Delta Lake pattern for geospatial joins and Z-ordering, though Mosaic itself is no longer in active development — for a new build, replicate the pattern using native H3 Python/SQL UDFs or Spark's built-in H3 expressions rather than depending on the retired Mosaic library [cite:32][cite:35].
- Convert address/point data (FCC Fabric) and polygon data (wire-center/jurisdiction boundaries) to H3 cells so that point-in-polygon joins become simple integer joins.
- Use Kepler.gl-style visualization or the Databricks App's mapping component (e.g., pydeck/deck.gl inside a Streamlit app) to render the H3 grid colored by risk score for the prioritization map screen.

## 3. Spark Declarative Pipelines (Lakeflow Declarative Pipelines)

- Define pipelines declaratively in Python or SQL; Spark handles dependency resolution, execution ordering, and incremental processing — you declare *what* data should exist, not the imperative steps [cite:17][cite:23].
- **Bronze layer**: raw ingested tables — FCC BDC/Fabric, simulated Lumen OSS exports, commodity prices, contractor registry, weather/soil.
- **Silver layer**: cleaned/conformed tables — deduplicated, schema-enforced, H3-indexed geometries, standardized jurisdiction codes.
- **Gold layer**: business-ready tables — `copper_retirement_readiness` (risk score per H3 cell/wire center), `commodity_price_features`, `contractor_scorecard`, `regulatory_requirements_by_jurisdiction`.
- Use **streaming tables** for near-real-time sources (incident feed, commodity prices) and **materialized views** for batch-refreshed aggregates (readiness scores) [cite:26].
- Automate via a Databricks Job schedule/trigger; use pipeline expectations (data quality constraints) at each layer to catch malformed FCC extracts or bad geometry early [cite:29].

## 4. Machine Learning + MLOps

Models in this build:
1. **Risk/readiness classifier** (per serving area) — gradient boosted trees.
2. **Sequencing optimizer** — constraint/LP solver, not a classic ML model, but log its scenario runs for auditability.
3. **Commodity price forecaster** — time-series model (gradient boosting or Prophet-style baseline) [cite:39][cite:42].
4. **Contractor scoring model** (optional stretch) — ranks contractors by fit.

MLOps practices to demonstrate:
- **Experiment tracking**: every training run logged to MLflow with parameters, metrics, and artifacts.
- **Model Registry**: promote models through Unity Catalog-governed stages (None → Staging → Production) with lineage back to the Gold training tables.
- **Model Serving**: deploy the readiness classifier and commodity forecaster as REST endpoints so the Databricks App and agents can call them live [cite:21].
- **Monitoring**: use Lakehouse Monitoring on inference tables to detect feature/prediction drift, particularly important for the volatile commodity forecast.
- **Reproducibility/governance**: because all training data lives in Unity Catalog-governed Delta tables, every model version has full data lineage — a point Databricks documentation emphasizes for agent/ML systems [cite:24].

## 5. Agents

Build four agents using **Agent Bricks / Mosaic AI Agent Framework** with the **Agent SDK**, evaluated via **MLflow Tracing** and **Agent Evaluation** before promotion [cite:18][cite:21][cite:24]:

1. **Regulatory Agent** — RAG over ingested FCC/state/local regulatory corpus, using Vector Search or **Lakebase Search** (native hybrid vector + full-text retrieval inside Lakebase Postgres, keeping agent retrieval and operational state on one backend) [cite:15].
2. **Dig-Triage Agent** — tool-calling agent that queries geospatial Gold tables, the Lakebase retirement plan, and a rerouting-lookup tool to recommend incident response actions.
3. **Contractor-Sourcing Agent** — queries the contractor registry joined to geospatial and incident data to shortlist crews.
4. **Supervisor Agent** — orchestrates the above three plus the commodity-forecast Model Serving endpoint, routing user/planner questions to the right specialist agent, following Databricks' documented supervisor-agent orchestration pattern [cite:24].

Build agents with the **AI Playground** for no-code prototyping first, then export to Python code for production hardening; register all four as **Agent Services** in Unity Catalog for discoverability and access control [cite:24].

## 6. Lakebase

- Lakebase is Databricks' fully managed, serverless Postgres for operational (OLTP) workloads, unifying transactional, analytical, and AI workloads without needing to move data out of the lakehouse — GA on AWS, beta on Azure as of early 2026 [cite:3][cite:6][cite:9][cite:12].
- Use Lakebase for tables that need frequent, low-latency read/write from apps and agents: `retirement_plan`, `dig_incidents`, `contractor_assignments`, `regulatory_checklist_status`.
- Use **Lakebase Search** (native `lakebase_vector` and `lakebase_text` Postgres extensions) so the Regulatory Agent's retrieval and the operational tables live in the same backend, simplifying the agent loop's architecture [cite:15].
- Sync Gold Lakehouse tables (readiness scores, forecasts) into Lakebase where the App needs to join analytical output with live operational state.

## 7. Databricks Apps

Build four app screens using Streamlit (or Dash/Gradio) deployed as Databricks Apps on serverless compute, integrated with Unity Catalog governance and OAuth [cite:31][cite:34][cite:43]:

1. **Prioritization Map** — H3 hex map colored by readiness/risk score, filterable by wave.
2. **Retirement Plan Tracker** — Gantt-style view of the multi-year roadmap, editable, backed by Lakebase `retirement_plan`.
3. **Dig-Triage Console** — incident intake form + live agent-recommended action list, backed by Lakebase `dig_incidents`.
4. **Commodity & Workforce Dashboard** — price forecast chart, sell/hold recommendation, contractor shortlist with assign/approve buttons.

Each app connects to Unity Catalog for governed reads of Gold tables and to Lakebase for low-latency operational reads/writes, and calls the deployed agent/model-serving endpoints for live recommendations [cite:31][cite:43].
