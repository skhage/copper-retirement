# Zero-Copper Plan — Prioritization & Roadmap Reference

## Objective
Design the analytics and ML layer that identifies low-risk areas to retire first and sequences the full portfolio down to zero copper, subject to regulatory, workforce, and capital constraints.

## Why "low-risk first" matters
Retiring low-risk segments first builds organizational muscle, generates early wins/case studies for regulators and customers, and avoids high-severity failures (e.g., hitting a hospital's only copper-fed alarm circuit) early in the program. Legacy 911, medical monitoring, alarm, and fax/credit-card-reader dependencies are explicitly called out in FCC guidance as compatibility checks carriers must satisfy before retiring copper [cite:8].

## Risk Scoring Dimensions
Build a composite "retirement readiness score" per wire-center / serving area (H3 hex or Census block group), combining:
- **Subscriber dependency**: active copper lines, POTS-only households, no fiber/FWA alternative available nearby.
- **Critical service overlap**: alarm systems, medical monitoring, 911 backup, fax/credit-card lines (flagged categories in FCC modernization guidance) [cite:8].
- **Fiber/alternative overbuild status**: whether fiber-to-the-premises or fixed wireless already passes the area (reduces risk — customers have a landing spot).
- **Regulatory friction**: state-level protections beyond the federal minimum, presence of active PUC dockets, Tribal land overlap [cite:8].
- **Physical/dig risk**: soil type, permitting complexity, presence of other utilities (gas, water, electric conduit) in the same corridor, historical dig-related incident rate in the area.
- **Commercial value of the copper**: linear feet of recoverable copper cable weighted by current scrap/wire price, informing which segments retiring first also yields the best near-term revenue (ties to `commodity-workforce.md`).

## Suggested Model Approach (MLOps-friendly)
- Treat prioritization as a two-stage problem: (1) a supervised/unsupervised **risk classifier** per serving area (gradient boosted trees on the features above, logged via MLflow, registered in Unity Catalog Model Registry), and (2) a **sequencing/optimization** layer (linear/integer programming or a constraint solver) that takes risk scores plus crew capacity, budget, and regulatory notice windows as inputs and outputs a rolling 2026–2029 retirement schedule.
- Version training data as Delta tables with Unity Catalog lineage so every model run is reproducible and auditable — a requirement Databricks documentation emphasizes for production agent/ML systems [cite:24].
- Retrain the risk classifier on a schedule (e.g., monthly) as new BDC filings, incident data, and dig outcomes arrive; use Lakehouse Monitoring to watch for feature and prediction drift.

## Data This Plan Consumes
- Gold "copper retirement readiness" table produced by the Spark Declarative Pipelines (see `technical-reference.md`).
- H3-indexed copper footprint proxy from FCC Fabric/BDC data (see `00-master-architecture.md` data-gap note) [cite:16][cite:28].
- Lumen internal OSS/GIS extracts (represent as a simulated/synthetic source in the demo, clearly labeled as such — do not fabricate real Lumen infrastructure data).

## Roadmap Output & Where It Lives
- The finalized multi-year schedule (which serving areas retire in which quarter) is written to a **Lakebase** Postgres table (`retirement_plan`) so the planning **Databricks App** can support live edits, comments, and status changes by planners without touching the Lakehouse Gold tables directly [cite:9].
- Every schedule change should be timestamped and versioned; expose plan-vs-actual variance (subscriber migration rate vs. plan) as a Gold table feeding a dashboard.

## Milestone Structure to Present in the Demo
1. **Wave 1 (Year 1)**: lowest-risk, highest fiber-overbuild-overlap serving areas — target for fastest 90-day-notice retirements under the new FCC rules [cite:5].
2. **Wave 2 (Years 2–3)**: medium-risk areas requiring some customer migration support and state coordination.
3. **Wave 3 (Years 3–4)**: highest-complexity areas — Tribal land, dense critical-service overlap, contested PUC dockets — requiring longest lead time.
4. **Zero-Copper Checkpoint**: define the Gold-table KPI ("active copper lines remaining" trending to zero) that the executive Databricks App dashboard tracks in real time.
