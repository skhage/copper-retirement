# Regulatory & Jurisdictional Reference

## Objective
Design the ingestion, retrieval, and agent layer that keeps Lumen compliant across federal, state, and local rules as it retires copper — and surfaces jurisdiction-specific requirements to planners before they schedule a retirement wave.

## Regulatory Landscape (as of Sept 2026)
- **Federal baseline**: the FCC's March 2026 "Network and Services Modernization Order" (FCC 26-19, adopted March 26, 2026) eliminated the Section 251(c)(5) network-change disclosure *FCC filing* and its public-notice/objection process for copper retirement, removing the prior FCC-run public-comment/challenge mechanism [cite:5][cite:11]. It did **not** eliminate Section 214(a) discontinuance authorization — instead it **streamlined** 214 (one consolidated tech-transition discontinuance rule, 31-day automatic grants, blanket authority to grandfather certain legacy services, and new 911-coordination requirements). This is a common misconception to avoid in the demo: 251(c)(5) filing review is gone; 214 authorization is streamlined but still required when a retirement causes a service discontinuance [cite:5][cite:11].
- **What remains federally**: carriers must still obtain Section 214 authorization when a retirement discontinues a service, give at least 90 days' direct written notice to residential retail customers before retiring copper, and provide direct notice to interconnecting carriers/911 service providers; public notice (e.g., on a publicly accessible website/industry fora) is still required even though the FCC filing/objection step is gone [cite:5][cite:8].
- **State/Tribal notice**: carriers must still notify the state governor, state PUC, and Tribal governments at least 180 days before retirement (90 days if there are no remaining customers on the copper) — this obligation is independent of the federal streamlining and is the main place state-level friction still lives [cite:8].
- **Consumer protections carried forward**: network performance/reliability must be substantially unchanged, 911/accessibility/cybersecurity standards must be met, and compatibility with legacy devices (alarms, medical monitors, credit-card readers, fax) must be assured before retirement [cite:8].
- **Backup power disclosure**: if copper is replaced by a non-powered-by-the-network technology, carriers must offer customers the option to purchase backup battery power (8-hour minimum, moving toward 24-hour) [cite:8].
- **Competitive/industry context**: Verizon, Frontier, and CenturyLink/Lumen are all filing copper retirement notices in parallel with target windows of 2026–2029, so state regulators are handling a wave of simultaneous filings — expect variable state responsiveness and potential local political sensitivity in low-density/rural areas [cite:10].

## Why This Needs an Agent, Not Just a Filing Tracker
Because the *federal* review step is gone but *state and local* requirements still vary (notice windows, PUC docket practices, franchise/right-of-way permitting rules, local historic-district or open-trenching ordinances), planners need a fast way to ask "what do I need to file/notify for wire center X in state Y before I schedule this dig" and get a synthesized answer grounded in current source documents rather than stale memory.

## Regulatory Agent Design
- **Corpus**: ingest FCC orders/public notices, state PUC tariff and copper-retirement rules, local right-of-way/permitting ordinances, and Lumen's own internal compliance playbooks (represent as a document corpus in the demo).
- **Retrieval**: index the corpus with Databricks Vector Search or Lakebase Search (hybrid vector + full-text, natively built into Lakebase Postgres) so the agent can do grounded retrieval-augmented generation over regulatory text alongside operational data in the same backend [cite:15].
- **Agent behavior**: given a serving area (H3 hex / wire center) and a proposed retirement date, the agent returns (1) required notice types and lead times, (2) which state/local bodies to notify, (3) any special critical-service compatibility checks required, and (4) a checklist status stored back to Lakebase for the planning app to display.
- **Governance**: register the agent in Unity Catalog as an Agent Service so compliance and legal teams can see exactly what data it's grounded in and audit every response via MLflow Tracing [cite:24].
- **Evaluation**: build a labeled test set of "regulatory question → correct citation" pairs; run Agent Evaluation with LLM-as-a-judge plus a legal-team human review step before allowing the agent's output to gate a retirement wave's go/no-go decision [cite:21][cite:24].

## Data Sources for Ingestion
- FCC Public Notices and Orders (e.g., WC Docket Nos. 25-208/25-209) [cite:5].
- FCC "What Government Officials Need to Know" guidance and the 2015 Tech Transitions Order [cite:8].
- State PUC dockets and tariff filings (state-by-state; ingest as they're published — build a generic connector pattern rather than hardcoding one state).
- Local municipal right-of-way/permitting portals (highly fragmented; treat as a longer-tail ingestion backlog item in the demo, not a v1 must-have).

## Demo Talking Point
Ask the agent: "We want to retire copper in [wire center] in Colorado in Q2 2027 — what do we need to file and by when?" and show it synthesizing the federal 90/180-day notice rule with the still-mandatory state PUC/governor notice, pulling directly from ingested source text rather than a hardcoded rule table [cite:5][cite:8].
