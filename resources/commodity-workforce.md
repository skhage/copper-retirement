# Commodity Timing & Contractor/Workforce Reference

## Objective
Design the ML forecasting and sourcing layer that (1) times the sale of recovered copper to maximize revenue and (2) identifies and scores contractors/vendors to perform the physical dig/removal work.

## Commodity Forecasting

### Market Context
Copper is actively traded on the London Metal Exchange (LME, priced per metric ton) and COMEX (priced per pound), with third-party forecasting services (e.g., Trading Economics) publishing quarterly and 12-month-forward consensus forecasts as reference benchmarks [cite:39][cite:45]. As of early September 2026, spot copper was trading near 6.59 USD/lb with a 12-month consensus forecast near 7.23 USD/lb, illustrating the kind of upward move that makes retirement *timing* — not just retirement itself — a real financial lever [cite:39].

### Data Sources
- LME copper (LME-XCU) rates API for exchange pricing [cite:33].
- Commodity price APIs (e.g., API Ninjas commodity price/historical endpoints) for OHLCV history to train forecasting models [cite:42].
- Trading Economics or similar for consensus analyst forecasts as a benchmark/sanity-check layer, not a replacement for your own model [cite:39][cite:45].
- Internal Lumen data on recovered copper volume/grade by retirement wave (simulate in the demo).

### Modeling Approach (MLOps-friendly)
- Frame as a time-series forecasting problem (e.g., gradient boosting on lagged prices/macro features, or a classical model like Prophet/ARIMA as a baseline) predicting copper price over a 3–18 month horizon to inform "sell now vs. hold" decisions per retirement wave.
- Log all experiments in MLflow, register the winning model in Unity Catalog Model Registry, and deploy via Model Serving so the forecast can be queried on demand from the commodity-timing Databricks App.
- Use Lakehouse Monitoring to track forecast error over time and trigger retraining when drift exceeds a threshold — critical for a market as volatile as copper.
- Combine the price forecast with the *volume* forecast coming out of the zero-copper retirement schedule (from `zero-copper-plan.md`) to produce a revenue-optimized selling schedule: e.g., "hold Wave 2's recovered copper an extra quarter if the forecast shows a price increase, given storage/carrying cost is low."

## Contractor & Workforce Sourcing

### The Problem
Because Verizon, Frontier, and CenturyLink/Lumen are all retiring copper on similar 2026–2029 timelines, qualified excavation/splicing contractor capacity will be contested across the industry [cite:10]. Lumen needs a systematic way to identify, qualify, and schedule contractors rather than relying on ad hoc regional relationships.

### Design
- **Ingestion**: build a contractor/vendor registry table (utility locator/excavation firms, telecom splicing crews, state contractor licensing databases where available) with fields for certifications, geographic coverage, safety incident history, and current price/rate cards.
- **Contractor-Sourcing Agent**: given a retirement wave's serving areas and schedule, the agent queries the registry (joined to the H3 geospatial layer) to recommend a ranked shortlist of contractors by proximity, certification match, capacity/availability, and past safety/incident performance (tie back to `dig-safe-triage.md` incident logs).
- **Where it's stored**: contractor assignments and bids are transactional, frequently updated records — store in **Lakebase** alongside the retirement plan and incident tables so the same operational database backs planning, triage, and sourcing workflows [cite:3][cite:9].
- **App surface**: a "Commodity & Workforce" Databricks App tab showing (1) the price forecast chart, (2) recommended sell/hold timing per wave, and (3) a contractor shortlist with assign/approve actions writing back to Lakebase.

## Demo Talking Points
- Show the forecasting model projecting copper price for the next two quarters and recommending Lumen delay selling Wave 1's recovered copper by one quarter, quantifying the revenue delta.
- Show the contractor-sourcing agent recommending three qualified crews for a specific wire center, factoring in a nearby past incident logged in the triage system.
