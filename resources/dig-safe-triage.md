# Dig-Safe Triage & Network Incident Routing Reference

## Objective
Design the real-time triage system that activates when a dig crew retiring copper accidentally damages adjacent infrastructure (fiber, gas, electric, water) or disrupts live network traffic still riding on copper being removed.

## The Core Problem
Retiring copper is inherently a physical excavation/splicing activity happening in shared utility corridors. Two failure modes matter for this demo:
1. **Utility strike**: dig crew hits gas/electric/water/unrelated fiber during copper removal.
2. **Live traffic disruption**: some circuits on the copper being retired (alarm, medical monitor, legacy business circuits, fax lines) are still active and get cut before migration is confirmed complete — the exact compatibility categories the FCC requires carriers to protect [cite:8].

## Triage Architecture (Agent-Orchestrated)
- **Trigger**: field technician or crew reports an incident via the Databricks App (mobile-friendly form) or a monitoring system flags a sudden circuit-down event.
- **Incident record**: written immediately to a **Lakebase** Postgres table (`dig_incidents`) for low-latency read/write — this is exactly the operational, transactional workload Lakebase is designed for, unifying OLTP state with the same governed platform as the analytics layer [cite:3][cite:9].
- **Triage Agent**: an agent (built with Databricks Agent Bricks / Mosaic AI Agent Framework, using tool-calling) that on incident creation:
  1. Queries the H3-indexed geospatial Gold table to find what else is in the same corridor/hex (other utilities, nearby customers, critical-service flags).
  2. Queries the retirement plan (Lakebase) to check whether affected circuits were supposed to be migrated already.
  3. Calls a **rerouting recommendation tool** — a function/UC tool that looks up alternate paths (e.g., nearest fiber node, wireless backup, alternate central office route) from the network topology table.
  4. Drafts a prioritized action list (e.g., "notify customer X, dispatch splice crew, activate backup battery/wireless failover") and writes it back to `dig_incidents`.
- **Supervisor Agent**: routes between the Triage Agent, the Regulatory Agent (if the incident triggers a new disclosure obligation), and the Contractor-Sourcing Agent (if emergency crew dispatch is needed) — this multi-agent-with-supervisor pattern is a documented Databricks pattern for orchestrating specialized agents [cite:24].
- **Human-in-the-loop**: all agent recommendations surface in the Databricks App triage console for a NOC/ops supervisor to approve before dispatch — align with Databricks' emphasis on human feedback and evaluation loops for production agents [cite:21][cite:24].

## Data Feeding the Triage Agent
- Network topology / circuit inventory (simulate as a Delta table representing central offices, fiber routes, and legacy circuit assignments).
- H3-indexed corridor data joining copper location, other utility lines, and critical-service flags (from `zero-copper-plan.md` risk features).
- Historical incident log (for the ML/agent to learn typical resolution paths and time-to-restore).
- Weather/soil/permit data if available, since dig risk correlates with these ingestion sources.

## MLOps & Evaluation Considerations
- Log every agent trace via MLflow Tracing so ops can audit why a rerouting recommendation was made — this is the standard Databricks pattern for agent observability [cite:24].
- Build a small labeled evaluation set of past incidents with the "correct" resolution path to run Agent Evaluation / LLM-as-a-judge scoring before promoting any triage-agent update to production [cite:21].
- Track online metrics: time-to-acknowledge, time-to-reroute-recommendation, false-positive rate on "critical service impacted" flags.

## Demo Talking Points
- Show a simulated incident: crew reports a cut wire; within seconds the agent surfaces "this hex has an active medical-monitoring line + no fiber alternative yet" and recommends holding the cut and dispatching a temporary wireless backup, referencing the FCC's required compatibility protections [cite:8].
- Show the same incident logged, triaged, and closed out entirely inside the Databricks App + Lakebase — no separate ticketing system needed.
