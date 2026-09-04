ic# Lumen Copper Retirement — Databricks Demo: Master Architecture

## Purpose
This is the anchor document for a Databricks demo built for Lumen Technologies (CenturyLink/Qwest legacy footprint) showing an end-to-end Data Intelligence Platform solution for retiring copper plant and migrating to fiber/fixed-wireless alternatives. Use this doc as the top-level index; the companion docs listed below go deeper on each workstream. Build order should follow the numbered phases.

## Business Context (why this matters now)
- Lumen has committed to decommissioning most legacy copper by the end of 2029 and stopped accepting move/add/change orders for POTS in legacy CenturyLink territory starting May 1, 2025 [cite:1].
- Lumen sold its consumer fiber business to AT&T for $5.75B in 2025 while retaining copper broadband/voice operations, and lost 310,000 legacy broadband subscribers (-21%) between Q4 2024 and Q4 2025 [cite:7].
- In March 2026 the FCC eliminated Section 214 discontinuance applications and Section 251(c)(5) network change disclosures for copper retirement, leaving a 90-day customer notice as the only remaining federal requirement — this materially compresses the achievable retirement timeline and raises the importance of good sequencing and local/state coordination [cite:5][cite:11].
- State PUCs, governors, and Tribal governments still require notice (180 days for interconnecting/non-residential, 90 days residential) even though the federal review process is gone, so state-by-state regulatory tracking remains essential [cite:8].
- Competing carriers (Verizon, Frontier, CenturyLink) are running parallel retirements through 2026–2029, meaning contractor/labor and commodity markets will be contested [cite:10].

## Demo Narrative (the story you tell in the room)
1. **Where is our copper, and what's the risk of touching it first?** (Ingestion + Geospatial + ML risk scoring)
2. **What's the sequenced, capital-efficient plan to zero copper?** (Spark Declarative Pipelines + ML optimization + Lakebase-backed planning app)
3. **If a dig crew hits something unexpected, how do we triage and reroute traffic fast?** (Agents + real-time network telemetry + Lakebase operational store)
4. **Are we clear on regulations in every jurisdiction we touch?** (Agent + document retrieval over FCC/state PUC corpus)
5. **Who do we hire to dig, and when do we sell recovered copper for the best price?** (Contractor/vendor data + commodity forecasting ML + Apps dashboard)

## Component-to-Workload Mapping

| Databricks Capability | Where It Fits in This Demo |
|---|---|
| Ingestion (Auto Loader, Lakeflow Connect, partner connectors) | Land FCC BDC/Fabric files, Lumen OSS/inventory exports, GIS shapefiles, weather/soil data, commodity price feeds, contractor/vendor registries, state PUC filings |
| Geospatial (H3 grid indexing, Mosaic-pattern ST_ functions, Kepler/Apps mapping) | Index copper plant location, wire-center boundaries, and permitting jurisdictions to a common H3 hex grid for joins and risk scoring |
| Spark Declarative Pipelines (Lakeflow Declarative Pipelines) | Bronze→Silver→Gold medallion pipeline turning raw ingestion into a governed "Copper Retirement Readiness" Gold layer |
| Machine Learning + MLOps (MLflow, Unity Catalog Model Registry, Model Serving, Lakehouse Monitoring) | Risk scoring model for dig areas, prioritization/sequencing optimizer, copper commodity price forecasting model |
| Agents (Agent Bricks, Mosaic AI Agent Framework, MCP, Genie, Vector Search) | Regulatory Q&A agent, dig-triage/incident-routing agent, contractor-sourcing agent, supervisor agent orchestrating all three |
| Lakebase (managed Postgres, OLTP + Lakebase Search) | Operational system of record for retirement plan status, incident tickets, contractor assignments, permit status — read/write from Apps and Agents with low latency |
| Databricks Apps (Streamlit/Dash/Gradio on serverless) | Field/ops-facing UI: prioritization map, retirement plan tracker, incident triage console, commodity timing dashboard |

## Build Phases
1. **Phase 0 — Data Foundation**: Unity Catalog setup, catalogs/schemas for bronze/silver/gold, external locations for raw files.
2. **Phase 1 — Ingestion**: land all sources described in the ingestion doc.
3. **Phase 2 — Geospatial Enrichment**: H3-index copper assets and jurisdictional boundaries.
4. **Phase 3 — Pipelines**: Spark Declarative Pipelines building Gold "copper retirement readiness" tables.
5. **Phase 4 — ML**: risk scoring, sequencing optimization, commodity forecasting, with MLflow + Model Registry + Serving + Monitoring.
6. **Phase 5 — Lakebase**: stand up operational Postgres schema for plan/ticket/vendor state.
7. **Phase 6 — Agents**: build regulatory, triage, and contractor-sourcing agents; wire into a supervisor agent.
8. **Phase 7 — Apps**: assemble the four Databricks Apps screens against Gold tables + Lakebase.

## Companion Documents
- `zero-copper-plan.md` — prioritization methodology and phased retirement roadmap
- `dig-safe-triage.md` — incident/routing triage architecture for network disruptions during excavation
- `regulatory-jurisdictions.md` — FCC/state PUC/local permitting research and the regulatory agent design
- `commodity-workforce.md` — copper price forecasting and contractor/vendor sourcing design
- `technical-reference.md` — deep technical reference for ingestion, geospatial, Spark Declarative Pipelines, ML/MLOps, agents, Lakebase, and Apps

## Known Data Gaps (be upfront with stakeholders)
- There is no single public dataset that shows exact Lumen copper cable routes underground; the closest public proxies are the FCC Broadband Serviceable Location Fabric and Broadband Data Collection (BDC) technology-by-location data, which show where Lumen reports copper-based (DSL/legacy) service today, not literal buried-cable geometry [cite:16][cite:22][cite:28].
- The Fabric's location-level detail is itself contested — researchers note limitations including retroactive record removal and no direct public fabric-layer geometry [cite:22]. Treat FCC-derived copper footprint as an approximation layer, and pair it with Lumen's own internal OSS/GIS exports in the real build.
