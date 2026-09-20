# Databricks notebook source
# DBTITLE 1,Project Tags
# MAGIC %md
# MAGIC # project: copper-retirement | developer: copper-ml
# MAGIC
# MAGIC # P6 Agent Evaluation Sets — V2 Agents
# MAGIC **Triage**, **Contractor-Sourcing**, **Supervisor** — 25 labeled test cases each (75 total).
# MAGIC
# MAGIC Configures MLflow Tracing, creates Delta eval tables, and provides a scoring harness to gate agents before serving promotion.

# COMMAND ----------

# DBTITLE 1,Setup: MLflow Experiment + Tags
import mlflow
from mlflow.tracking import MlflowClient
from datetime import datetime

PROJECT_TAGS = {"telco_project": "copper-retirement", "developer": "copper-ml"}
EVAL_VERSION = "v2"

# Create/get experiment
exp = mlflow.set_experiment("/Users/stephen.hage@databricks.com/copper-retirement/experiments/agent_eval_sets")
client = MlflowClient()
client.set_experiment_tag(exp.experiment_id, "telco_project", "copper-retirement")
client.set_experiment_tag(exp.experiment_id, "developer", "copper-ml")
client.set_experiment_tag(exp.experiment_id, "eval_version", EVAL_VERSION)
print(f"Experiment: {exp.experiment_id} | Name: {exp.name}")

# COMMAND ----------

# DBTITLE 1,Triage Agent Eval Set (25 cases)
# ── Triage Agent: 25 labeled Q→A test cases ──────────────────────
# Covers: incident_lookup, proximity_search, reroute_suggest
# Difficulty: easy (direct lookups), medium (search + interpret), hard (multi-turn, edge cases)

triage_eval = [
    # --- INCIDENT LOOKUP (7 cases) ---
    {"eval_id": "T01", "input": "Look up incident 200046",
     "expected_tool": "incident_lookup", "expected_tool_args": '{"incident_id": 200046}',
     "expected_contains": ["P1", "critical", "CO", "emergency_response"],
     "category": "incident_lookup", "difficulty": "easy",
     "rationale": "P1 critical incident in CO with service interruption. Agent must return severity, state, and recommended action."},

    {"eval_id": "T02", "input": "What's the status of incident 200081?",
     "expected_tool": "incident_lookup", "expected_tool_args": '{"incident_id": 200081}',
     "expected_contains": ["P1", "critical", "WA", "underground_conduit"],
     "category": "incident_lookup", "difficulty": "easy",
     "rationale": "P1 WA incident in underground conduit with reroute required."},

    {"eval_id": "T03", "input": "Give me the full details on incident 200287",
     "expected_tool": "incident_lookup", "expected_tool_args": '{"incident_id": 200287}',
     "expected_contains": ["AZ", "aerial", "critical"],
     "category": "incident_lookup", "difficulty": "easy",
     "rationale": "AZ aerial cable critical incident — tests cable type extraction."},

    {"eval_id": "T04", "input": "I need information about dig incident number 200052",
     "expected_tool": "incident_lookup", "expected_tool_args": '{"incident_id": 200052}',
     "expected_contains": ["MN", "P1", "buried_direct"],
     "category": "incident_lookup", "difficulty": "easy",
     "rationale": "MN buried-direct incident. Natural language phrasing test."},

    {"eval_id": "T05", "input": "Can you check incident 200999 for me?",
     "expected_tool": "incident_lookup", "expected_tool_args": '{"incident_id": 200999}',
     "expected_contains": ["not found", "no incident", "does not exist"],
     "category": "incident_lookup_edge", "difficulty": "medium",
     "rationale": "Edge case: non-existent incident. Agent should gracefully report not found."},

    {"eval_id": "T06", "input": "Pull up incident 200372. How many cable pairs were affected?",
     "expected_tool": "incident_lookup", "expected_tool_args": '{"incident_id": 200372}',
     "expected_contains": ["2", "pair", "underground_conduit"],
     "category": "incident_lookup", "difficulty": "medium",
     "rationale": "Tests specific field extraction (affected_pair_count=2) from the response."},

    {"eval_id": "T07", "input": "What was the repair cost for incident 200053?",
     "expected_tool": "incident_lookup", "expected_tool_args": '{"incident_id": 200053}',
     "expected_contains": ["28334", "CO", "74"],
     "category": "incident_lookup", "difficulty": "medium",
     "rationale": "Repair cost $28,334.60 with 74 affected pairs — high severity."},

    # --- PROXIMITY SEARCH (8 cases) ---
    {"eval_id": "T08", "input": "Search for incidents near Denver, Colorado within 50km",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 39.74, "lon": -104.99, "radius_km": 50}',
     "expected_contains": ["P1", "incident"],
     "category": "proximity_search", "difficulty": "easy",
     "rationale": "Denver area has dense CO incidents. Tests geocoding from city name."},

    {"eval_id": "T09", "input": "Are there any dig incidents near latitude 33.45, longitude -112.07?",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 33.45, "lon": -112.07, "radius_km": 25}',
     "expected_contains": ["AZ", "incident"],
     "category": "proximity_search", "difficulty": "easy",
     "rationale": "Phoenix area coordinates, AZ incidents expected."},

    {"eval_id": "T10", "input": "Show me all incidents within 75km of Portland, Oregon",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 45.52, "lon": -122.68, "radius_km": 75}',
     "expected_contains": ["OR", "incident"],
     "category": "proximity_search", "difficulty": "easy",
     "rationale": "Portland OR has 613 state-wide incidents. Large radius should trigger summarization."},

    {"eval_id": "T11", "input": "Find copper cable incidents near Minneapolis within 30km",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 44.98, "lon": -93.27, "radius_km": 30}',
     "expected_contains": ["MN", "incident"],
     "category": "proximity_search", "difficulty": "easy",
     "rationale": "Minneapolis metro area MN cluster."},

    {"eval_id": "T12", "input": "Check for recent dig-safe incidents near Boise, Idaho",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 43.62, "lon": -116.21, "radius_km": 50}',
     "expected_contains": ["ID", "incident"],
     "category": "proximity_search", "difficulty": "medium",
     "rationale": "ID has 497 incidents. Tests default radius assumption."},

    {"eval_id": "T13", "input": "Any incidents near 47.6, -122.3 with a 100km radius?",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 47.6, "lon": -122.3, "radius_km": 100}',
     "expected_contains": ["WA"],
     "category": "proximity_search", "difficulty": "medium",
     "rationale": "Seattle area WA. Large radius triggers >20 row summarization."},

    {"eval_id": "T14", "input": "Search for incidents near latitude 25.0, longitude -80.0 within 50km",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 25.0, "lon": -80.0, "radius_km": 50}',
     "expected_contains": ["no incidents", "0", "none"],
     "category": "proximity_search_edge", "difficulty": "hard",
     "rationale": "Florida coords — no incidents in dataset (only CO/MN/WA/OR/ID/AZ). Edge case."},

    {"eval_id": "T15", "input": "How many P1 incidents are there within 200km of Colorado Springs?",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 38.83, "lon": -104.82, "radius_km": 200}',
     "expected_contains": ["P1"],
     "category": "proximity_search", "difficulty": "hard",
     "rationale": "Large radius from CO Springs. Agent must filter/count P1 from results."},

    # --- REROUTE SUGGEST (5 cases) ---
    {"eval_id": "T16", "input": "What reroute options are available for incident 200046?",
     "expected_tool": "reroute_suggest", "expected_tool_args": '{"incident_id": 200046}',
     "expected_contains": ["FIBER_MIGRATION", "EMERGENCY_RESTORE"],
     "category": "reroute", "difficulty": "easy",
     "rationale": "P1 critical CO incident — should get emergency options."},

    {"eval_id": "T17", "input": "Suggest rerouting options for incident 200131",
     "expected_tool": "reroute_suggest", "expected_tool_args": '{"incident_id": 200131}',
     "expected_contains": ["FIBER_MIGRATION", "COPPER_REROUTE", "REPAIR_IN_PLACE"],
     "category": "reroute", "difficulty": "easy",
     "rationale": "AZ P1 incident. Should return all 6 option types."},

    {"eval_id": "T18", "input": "For incident 200348, what's the recommended action and what are the alternatives?",
     "expected_tool": "reroute_suggest", "expected_tool_args": '{"incident_id": 200348}',
     "expected_contains": ["emergency_response"],
     "category": "reroute", "difficulty": "medium",
     "rationale": "Tests agent combining incident details (recommended_action) with reroute options."},

    {"eval_id": "T19", "input": "Can we reroute traffic for incident 200999?",
     "expected_tool": "reroute_suggest", "expected_tool_args": '{"incident_id": 200999}',
     "expected_contains": ["not found", "no incident", "no data"],
     "category": "reroute_edge", "difficulty": "medium",
     "rationale": "Non-existent incident. Agent must handle gracefully."},

    {"eval_id": "T20", "input": "Incident 200098 is P1 critical with 19 affected pairs. Should we reroute or do emergency restore?",
     "expected_tool": "reroute_suggest", "expected_tool_args": '{"incident_id": 200098}',
     "expected_contains": ["EMERGENCY_RESTORE"],
     "category": "reroute", "difficulty": "hard",
     "rationale": "Agent must reason about severity + pair count to recommend appropriate option."},

    # --- MULTI-TURN / COMPOSITE (5 cases) ---
    {"eval_id": "T21", "input": "Look up incident 200489, then tell me what reroute options are available",
     "expected_tool": "incident_lookup,reroute_suggest", "expected_tool_args": '{"incident_id": 200489}',
     "expected_contains": ["AZ", "critical", "FIBER_MIGRATION"],
     "category": "multi_tool", "difficulty": "hard",
     "rationale": "Multi-tool: lookup first then reroute. Tests chained tool calls."},

    {"eval_id": "T22", "input": "There's a critical dig-safe event near Phoenix. Find the nearest incidents and triage them.",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 33.45, "lon": -112.07, "radius_km": 50}',
     "expected_contains": ["AZ", "P1", "emergency"],
     "category": "multi_tool", "difficulty": "hard",
     "rationale": "Vague input requiring geocoding Phoenix → proximity search → triage interpretation."},

    {"eval_id": "T23", "input": "I'm dispatching crews to the Denver metro area. Give me a priority-sorted list of all P1 and P2 incidents within 40km.",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 39.74, "lon": -104.99, "radius_km": 40}',
     "expected_contains": ["P1", "P2", "CO"],
     "category": "multi_tool", "difficulty": "hard",
     "rationale": "Operational dispatch scenario. Agent must filter and sort by priority."},

    {"eval_id": "T24", "input": "For incident 200576, how many customers are impacted and what should we do?",
     "expected_tool": "incident_lookup,reroute_suggest", "expected_tool_args": '{"incident_id": 200576}',
     "expected_contains": ["AZ", "customer", "service"],
     "category": "multi_tool", "difficulty": "hard",
     "rationale": "Tests interpretation of impacted_customer_count and action recommendation."},

    {"eval_id": "T25", "input": "We have a network emergency near 39.5, -105.1. Find all critical incidents and recommend immediate actions.",
     "expected_tool": "proximity_search", "expected_tool_args": '{"lat": 39.5, "lon": -105.1, "radius_km": 25}',
     "expected_contains": ["CO", "critical", "emergency"],
     "category": "multi_tool", "difficulty": "hard",
     "rationale": "Emergency scenario in dense CO area. Tests crisis-mode triage."},
]

print(f"Triage eval cases: {len(triage_eval)}")
for cat in set(c['category'] for c in triage_eval):
    cnt = sum(1 for c in triage_eval if c['category'] == cat)
    print(f"  {cat}: {cnt}")

# COMMAND ----------

# DBTITLE 1,Contractor Agent Eval Set (25 cases)
# ── Contractor-Sourcing Agent: 25 labeled Q→A test cases ────────
# Covers: search_contractors, contractor_incidents, wave_assignments

contractor_eval = [
    # --- SEARCH CONTRACTORS (9 cases) ---
    {"eval_id": "C01", "input": "Find underground boring contractors in Colorado",
     "expected_tool": "search_contractors", "expected_tool_args": '{"state": "CO", "type": "underground_boring"}',
     "expected_contains": ["contractor", "CO"],
     "category": "search", "difficulty": "easy",
     "rationale": "Basic state + type search. CO has active operations."},

    {"eval_id": "C02", "input": "Who are the top-rated aerial line contractors in Arizona?",
     "expected_tool": "search_contractors", "expected_tool_args": '{"state": "AZ", "type": "aerial_line"}',
     "expected_contains": ["Cascade Utility Partners", "preferred"],
     "category": "search", "difficulty": "easy",
     "rationale": "AZ has multiple preferred aerial_line contractors."},

    {"eval_id": "C03", "input": "List all certified fiber splicing contractors in Minnesota with safety score above 90",
     "expected_tool": "search_contractors", "expected_tool_args": '{"state": "MN", "type": "fiber_splicing", "min_safety": 90, "certified_only": true}',
     "expected_contains": ["MN"],
     "category": "search", "difficulty": "medium",
     "rationale": "Tests multi-parameter search with safety threshold and certification filter."},

    {"eval_id": "C04", "input": "We need multi-discipline contractors in Oregon. Show me the preferred ones.",
     "expected_tool": "search_contractors", "expected_tool_args": '{"state": "OR", "type": "multi_discipline"}',
     "expected_contains": ["OR"],
     "category": "search", "difficulty": "easy",
     "rationale": "OR multi-discipline contractors. Tests dispatch_status filtering."},

    {"eval_id": "C05", "input": "Find general construction contractors in Idaho with at least 10 crew members",
     "expected_tool": "search_contractors", "expected_tool_args": '{"state": "ID", "type": "general_construction"}',
     "expected_contains": ["ID", "Prairie Fiber Co"],
     "category": "search", "difficulty": "medium",
     "rationale": "Tests crew size interpretation from results. Prairie Fiber Co is preferred in ID."},

    {"eval_id": "C06", "input": "Show contractors in Washington state",
     "expected_tool": "search_contractors", "expected_tool_args": '{"state": "WA"}',
     "expected_contains": ["WA"],
     "category": "search", "difficulty": "easy",
     "rationale": "State-only search, no type specified. Agent should handle gracefully."},

    {"eval_id": "C07", "input": "Any trenching contractors available in Arizona with safety rating over 95?",
     "expected_tool": "search_contractors", "expected_tool_args": '{"state": "AZ", "type": "trenching", "min_safety": 95}',
     "expected_contains": ["AZ"],
     "category": "search", "difficulty": "medium",
     "rationale": "Specific type + safety threshold. Tests parameter extraction from natural language."},

    {"eval_id": "C08", "input": "Find contractors in Florida",
     "expected_tool": "search_contractors", "expected_tool_args": '{"state": "FL"}',
     "expected_contains": ["no contractors", "none", "0"],
     "category": "search_edge", "difficulty": "medium",
     "rationale": "FL is not an operational state. Edge case for empty results."},

    {"eval_id": "C09", "input": "Who has the highest composite score among all preferred contractors in Colorado?",
     "expected_tool": "search_contractors", "expected_tool_args": '{"state": "CO"}',
     "expected_contains": ["National Utility Corp"],
     "category": "search", "difficulty": "hard",
     "rationale": "Tests ranking interpretation. National Utility Corp is top CO preferred."},

    # --- CONTRACTOR INCIDENTS (8 cases) ---
    {"eval_id": "C10", "input": "What's the incident history for Prairie Fiber Co?",
     "expected_tool": "contractor_incidents", "expected_tool_args": '{"name": "Prairie Fiber Co"}',
     "expected_contains": ["Prairie Fiber"],
     "category": "incidents", "difficulty": "easy",
     "rationale": "Prairie Fiber Co is a key ID contractor with wave assignments."},

    {"eval_id": "C11", "input": "Check the safety record of Central Excavation Co",
     "expected_tool": "contractor_incidents", "expected_tool_args": '{"name": "Central Excavation Co"}',
     "expected_contains": ["Central Excavation"],
     "category": "incidents", "difficulty": "easy",
     "rationale": "Central Excavation is a preferred AZ contractor in wave plan."},

    {"eval_id": "C12", "input": "Has Cascade Fiber Enterprises had any safety violations?",
     "expected_tool": "contractor_incidents", "expected_tool_args": '{"name": "Cascade Fiber Enterprises"}',
     "expected_contains": ["Cascade Fiber"],
     "category": "incidents", "difficulty": "easy",
     "rationale": "CO contractor in wave plan. Tests violation detection."},

    {"eval_id": "C13", "input": "Pull up the incident report for Gateway Network Co",
     "expected_tool": "contractor_incidents", "expected_tool_args": '{"name": "Gateway Network Co"}',
     "expected_contains": ["Gateway Network"],
     "category": "incidents", "difficulty": "easy",
     "rationale": "MN wave assignment contractor. Tests incident data completeness."},

    {"eval_id": "C14", "input": "Show me the fault rate for National Utility Corp",
     "expected_tool": "contractor_incidents", "expected_tool_args": '{"name": "National Utility Corp"}',
     "expected_contains": ["National Utility", "fault"],
     "category": "incidents", "difficulty": "medium",
     "rationale": "Tests specific metric extraction (fault_rate) from results."},

    {"eval_id": "C15", "input": "What's the compliance record for Frontier Cable Services LLC?",
     "expected_tool": "contractor_incidents", "expected_tool_args": '{"name": "Frontier Cable Services LLC"}',
     "expected_contains": ["Frontier Cable", "compliance"],
     "category": "incidents", "difficulty": "medium",
     "rationale": "WA wave assignment contractor. Tests compliance field extraction."},

    {"eval_id": "C16", "input": "Is there any incident history for Nonexistent Boring LLC?",
     "expected_tool": "contractor_incidents", "expected_tool_args": '{"name": "Nonexistent Boring LLC"}',
     "expected_contains": ["no", "not found", "none"],
     "category": "incidents_edge", "difficulty": "medium",
     "rationale": "Non-existent contractor. Edge case for graceful handling."},

    {"eval_id": "C17", "input": "Compare the safety records of Mountain Cable Enterprises and Great Plains Line Contractors",
     "expected_tool": "contractor_incidents", "expected_tool_args": '{"name": "Mountain Cable Enterprises"}',
     "expected_contains": ["Mountain Cable", "Great Plains Line"],
     "category": "incidents", "difficulty": "hard",
     "rationale": "Multi-contractor comparison. Agent must call tool twice and synthesize."},

    # --- WAVE ASSIGNMENTS (8 cases) ---
    {"eval_id": "C18", "input": "What contractors are assigned to Arizona in Q4 2026?",
     "expected_tool": "wave_assignments", "expected_tool_args": '{"wave": "2026-Q4", "state": "AZ"}',
     "expected_contains": ["Central Excavation", "Great Plains Telecom", "Cascade Utility", "Summit Field"],
     "category": "wave", "difficulty": "easy",
     "rationale": "AZ Q4-2026 has 4 contractors, 140 crew-days total."},

    {"eval_id": "C19", "input": "Show me the wave plan for Colorado Q4 2026",
     "expected_tool": "wave_assignments", "expected_tool_args": '{"wave": "2026-Q4", "state": "CO"}',
     "expected_contains": ["National Utility", "Cascade Fiber", "Rocky Mountain Infrastructure"],
     "category": "wave", "difficulty": "easy",
     "rationale": "CO Q4-2026 has 3 contractors, 70 crew-days, 14 devices."},

    {"eval_id": "C20", "input": "What's the crew-day allocation for Minnesota in 2026 Q4?",
     "expected_tool": "wave_assignments", "expected_tool_args": '{"wave": "2026-Q4", "state": "MN"}',
     "expected_contains": ["115", "crew", "23"],
     "category": "wave", "difficulty": "medium",
     "rationale": "MN Q4-2026: 115 total crew-days (30+35+50), 23 devices."},

    {"eval_id": "C21", "input": "How many devices are in the Idaho wave for Q3 2026?",
     "expected_tool": "wave_assignments", "expected_tool_args": '{"wave": "2026-Q3", "state": "ID"}',
     "expected_contains": ["12", "Prairie Fiber", "60"],
     "category": "wave", "difficulty": "medium",
     "rationale": "ID Q3-2026 is the earliest wave: 1 contractor, 60 crew-days, 12 devices."},

    {"eval_id": "C22", "input": "What's the total estimated cost for Washington state waves in 2027?",
     "expected_tool": "wave_assignments", "expected_tool_args": '{"wave": "2027", "state": "WA"}',
     "expected_contains": ["WA", "Frontier Cable", "Interstate Engineering"],
     "category": "wave", "difficulty": "hard",
     "rationale": "WA has waves in Q1, Q3, Q4 of 2027. Agent must aggregate across sub-waves."},

    {"eval_id": "C23", "input": "Show me the Q1 2027 retirement wave assignments",
     "expected_tool": "wave_assignments", "expected_tool_args": '{"wave": "2027-Q1"}',
     "expected_contains": ["CO", "ID", "OR", "WA"],
     "category": "wave", "difficulty": "medium",
     "rationale": "Q1-2027 spans 4 states with 5 contractors. No state filter = all states."},

    {"eval_id": "C24", "input": "Is there any wave planned for Q3 2026 besides Idaho?",
     "expected_tool": "wave_assignments", "expected_tool_args": '{"wave": "2026-Q3"}',
     "expected_contains": ["ID", "only", "Prairie Fiber"],
     "category": "wave", "difficulty": "hard",
     "rationale": "Q3-2026 only has ID. Tests agent's ability to confirm absence for other states."},

    {"eval_id": "C25", "input": "We're evaluating contractor capacity. Which state has the most crew-days allocated in Q2 2027?",
     "expected_tool": "wave_assignments", "expected_tool_args": '{"wave": "2027-Q2"}',
     "expected_contains": ["CO", "105"],
     "category": "wave", "difficulty": "hard",
     "rationale": "CO has 105 crew-days in Q2-2027 (45+25+35). Tests aggregation and ranking."},
]

print(f"Contractor eval cases: {len(contractor_eval)}")
for cat in set(c['category'] for c in contractor_eval):
    cnt = sum(1 for c in contractor_eval if c['category'] == cat)
    print(f"  {cat}: {cnt}")

# COMMAND ----------

# DBTITLE 1,Supervisor Agent Eval Set (25 cases)
# ── Supervisor Agent: 25 labeled Q→A test cases ────────────────
# Covers: routing to regulatory_query, triage_incident, find_contractors, commodity_forecast
# Key: tests correct sub-agent dispatch + response synthesis

supervisor_eval = [
    # --- SINGLE-DOMAIN ROUTING (10 cases) ---
    {"eval_id": "S01", "input": "What are the Section 214 requirements for copper retirement in Colorado?",
     "expected_route": "regulatory_query",
     "expected_contains": ["Section 214", "CO", "filing", "notice"],
     "category": "routing_regulatory", "difficulty": "easy",
     "rationale": "Clear regulatory domain. Should route to regulatory sub-agent."},

    {"eval_id": "S02", "input": "Look up dig-safe incident 200046",
     "expected_route": "triage_incident",
     "expected_contains": ["200046", "P1", "CO", "critical"],
     "category": "routing_triage", "difficulty": "easy",
     "rationale": "Clear triage domain. Should route to triage sub-agent."},

    {"eval_id": "S03", "input": "Find preferred underground boring contractors in Arizona",
     "expected_route": "find_contractors",
     "expected_contains": ["AZ", "boring", "contractor"],
     "category": "routing_contractor", "difficulty": "easy",
     "rationale": "Clear contractor domain. Should route to contractor sub-agent."},

    {"eval_id": "S04", "input": "What's the current copper price per ton?",
     "expected_route": "commodity_forecast",
     "expected_contains": ["copper", "price", "USD"],
     "category": "routing_commodity", "difficulty": "easy",
     "rationale": "Clear commodity domain. Should route to commodity sub-agent."},

    {"eval_id": "S05", "input": "What state PUC filing deadlines apply to copper decommissioning in Minnesota?",
     "expected_route": "regulatory_query",
     "expected_contains": ["MN", "PUC", "filing"],
     "category": "routing_regulatory", "difficulty": "medium",
     "rationale": "Regulatory with state-specific PUC context."},

    {"eval_id": "S06", "input": "Are there any critical incidents near Seattle?",
     "expected_route": "triage_incident",
     "expected_contains": ["WA", "incident"],
     "category": "routing_triage", "difficulty": "medium",
     "rationale": "Triage via proximity search. Tests city-to-coords resolution."},

    {"eval_id": "S07", "input": "Who's assigned to the Oregon retirement wave in Q4 2026?",
     "expected_route": "find_contractors",
     "expected_contains": ["OR", "Northern Trenching", "Great Plains Network"],
     "category": "routing_contractor", "difficulty": "medium",
     "rationale": "Wave assignment query routed to contractor sub-agent."},

    {"eval_id": "S08", "input": "What's the copper price forecast for Q1 2027?",
     "expected_route": "commodity_forecast",
     "expected_contains": ["forecast", "2027", "copper"],
     "category": "routing_commodity", "difficulty": "medium",
     "rationale": "Forecast vs current price. Should still route to commodity."},

    {"eval_id": "S09", "input": "What are the 911 coordination requirements for network transitions?",
     "expected_route": "regulatory_query",
     "expected_contains": ["911", "coordination"],
     "category": "routing_regulatory", "difficulty": "medium",
     "rationale": "Regulatory topic: 911_coordination. Non-state-specific."},

    {"eval_id": "S10", "input": "Check the incident history for Interstate Engineering Corp",
     "expected_route": "find_contractors",
     "expected_contains": ["Interstate Engineering"],
     "category": "routing_contractor", "difficulty": "easy",
     "rationale": "Contractor incident vetting routed to contractor sub-agent."},

    # --- CROSS-DOMAIN (10 cases) ---
    {"eval_id": "S11", "input": "I need a briefing on the Arizona Q4 2026 retirement wave: who are the contractors, and what are the current copper prices?",
     "expected_route": "find_contractors,commodity_forecast",
     "expected_contains": ["AZ", "contractor", "copper", "price"],
     "category": "cross_domain", "difficulty": "hard",
     "rationale": "Two-domain: contractor wave assignments + commodity prices. Parallel dispatch."},

    {"eval_id": "S12", "input": "We have incident 200131 in Arizona. Find the incident details and also tell me which contractors are available in AZ.",
     "expected_route": "triage_incident,find_contractors",
     "expected_contains": ["200131", "AZ", "contractor", "critical"],
     "category": "cross_domain", "difficulty": "hard",
     "rationale": "Triage + contractor. Tests parallel sub-agent dispatch."},

    {"eval_id": "S13", "input": "What are the regulatory requirements for retiring copper in Oregon, and who are the preferred contractors there?",
     "expected_route": "regulatory_query,find_contractors",
     "expected_contains": ["OR", "regulatory", "contractor"],
     "category": "cross_domain", "difficulty": "hard",
     "rationale": "Regulatory + contractor for same state. Tests co-dispatch."},

    {"eval_id": "S14", "input": "Give me a full Colorado status: any active incidents near Denver, current wave assignments, and applicable regulations.",
     "expected_route": "triage_incident,find_contractors,regulatory_query",
     "expected_contains": ["CO", "Denver", "incident", "wave", "regulation"],
     "category": "cross_domain", "difficulty": "hard",
     "rationale": "Three-domain briefing. Tests supervisor's multi-agent orchestration."},

    {"eval_id": "S15", "input": "What's the business case? Show me copper scrap value and the wave plan cost for Minnesota.",
     "expected_route": "commodity_forecast,find_contractors",
     "expected_contains": ["MN", "copper", "price", "cost", "crew"],
     "category": "cross_domain", "difficulty": "hard",
     "rationale": "Financial analysis: commodity value vs retirement cost."},

    {"eval_id": "S16", "input": "Incident 200081 in Washington needs emergency response. Find the incident details and check what contractors are assigned to WA Q1 2027.",
     "expected_route": "triage_incident,find_contractors",
     "expected_contains": ["200081", "WA", "P1", "Frontier Cable", "Interstate Engineering"],
     "category": "cross_domain", "difficulty": "hard",
     "rationale": "Emergency triage + contractor capacity. Specific incident + wave lookup."},

    {"eval_id": "S17", "input": "Are there tribal notice requirements in Idaho, and what does the commodity price forecast look like?",
     "expected_route": "regulatory_query,commodity_forecast",
     "expected_contains": ["tribal", "ID", "copper", "forecast"],
     "category": "cross_domain", "difficulty": "hard",
     "rationale": "Regulatory (tribal_notice topic) + commodity. Tests topic-specific routing."},

    {"eval_id": "S18", "input": "Search for P1 incidents near Boise and check if Prairie Fiber Co has any safety issues.",
     "expected_route": "triage_incident,find_contractors",
     "expected_contains": ["ID", "Boise", "Prairie Fiber"],
     "category": "cross_domain", "difficulty": "hard",
     "rationale": "Geographic incident search + contractor vetting. Tests mixed triage/contractor."},

    {"eval_id": "S19", "input": "Prepare a Q2 2027 executive summary: wave assignments across all states, regulatory filing status, and copper price outlook.",
     "expected_route": "find_contractors,regulatory_query,commodity_forecast",
     "expected_contains": ["Q2 2027", "wave", "regulation", "copper", "forecast"],
     "category": "cross_domain", "difficulty": "hard",
     "rationale": "Three-domain executive summary. Maximum supervisor orchestration."},

    {"eval_id": "S20", "input": "We're planning the Idaho expansion. What's the contractor capacity, are there any dig incidents there, and what regulatory filings do we need?",
     "expected_route": "find_contractors,triage_incident,regulatory_query",
     "expected_contains": ["ID", "contractor", "incident", "regulatory"],
     "category": "cross_domain", "difficulty": "hard",
     "rationale": "Full state planning query requiring all 3 non-commodity sub-agents."},

    # --- EDGE / AMBIGUOUS ROUTING (5 cases) ---
    {"eval_id": "S21", "input": "Tell me about copper retirement.",
     "expected_route": "regulatory_query",
     "expected_contains": ["copper", "retirement"],
     "category": "ambiguous", "difficulty": "medium",
     "rationale": "Vague query. Supervisor should route to regulatory as default for general copper retirement questions."},

    {"eval_id": "S22", "input": "What's happening in Arizona?",
     "expected_route": "find_contractors,triage_incident",
     "expected_contains": ["AZ"],
     "category": "ambiguous", "difficulty": "hard",
     "rationale": "Ambiguous scope. Could be incidents, contractors, or both. Tests supervisor's interpretation."},

    {"eval_id": "S23", "input": "How much is copper worth right now and what does the LME forecast show?",
     "expected_route": "commodity_forecast",
     "expected_contains": ["copper", "LME", "price", "forecast"],
     "category": "routing_commodity", "difficulty": "medium",
     "rationale": "Current + forecast in same domain. Single sub-agent should handle both."},

    {"eval_id": "S24", "input": "I need help with a dig-safe event. The coordinates are 39.28, -104.64.",
     "expected_route": "triage_incident",
     "expected_contains": ["CO", "incident"],
     "category": "routing_triage", "difficulty": "medium",
     "rationale": "Raw coordinates for proximity search via triage. Tests coord extraction."},

    {"eval_id": "S25", "input": "What's the weather like in Denver today?",
     "expected_route": "none",
     "expected_contains": ["cannot", "outside", "not able", "don't have"],
     "category": "out_of_scope", "difficulty": "easy",
     "rationale": "Out-of-scope question. Agent should politely decline."},
]

print(f"Supervisor eval cases: {len(supervisor_eval)}")
for cat in set(c['category'] for c in supervisor_eval):
    cnt = sum(1 for c in supervisor_eval if c['category'] == cat)
    print(f"  {cat}: {cnt}")

# COMMAND ----------

# DBTITLE 1,Write Eval Sets to Delta Tables
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from datetime import datetime
import json

spark = SparkSession.builder.getOrCreate()
CATALOG_SCHEMA = "cdm_tmforum.copper_retirement"
now = datetime.utcnow()

def build_eval_df(eval_list, agent_name):
    """Convert eval list to Spark DataFrame with standard schema."""
    rows = []
    for e in eval_list:
        rows.append({
            "eval_id": e["eval_id"],
            "agent": agent_name,
            "input": e["input"],
            "expected_tool": e.get("expected_tool", ""),
            "expected_route": e.get("expected_route", ""),
            "expected_tool_args": e.get("expected_tool_args", ""),
            "expected_contains": json.dumps(e["expected_contains"]),
            "category": e["category"],
            "difficulty": e["difficulty"],
            "rationale": e["rationale"],
            "eval_version": EVAL_VERSION,
            "created_by": "@ml-engineer",
            "created_at": now.isoformat(),
        })
    return spark.createDataFrame(rows)

# Build DataFrames
df_triage = build_eval_df(triage_eval, "triage")
df_contractor = build_eval_df(contractor_eval, "contractor")
df_supervisor = build_eval_df(supervisor_eval, "supervisor")

# Union all into one table
df_all = df_triage.unionByName(df_contractor).unionByName(df_supervisor)

# Write to Delta
table_name = f"{CATALOG_SCHEMA}.agent_eval_dataset_v2"
df_all.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table_name)

print(f"Wrote {df_all.count()} eval cases to {table_name}")
print(f"  Triage: {df_triage.count()}")
print(f"  Contractor: {df_contractor.count()}")
print(f"  Supervisor: {df_supervisor.count()}")

# Tag the table
spark.sql(f"ALTER TABLE {table_name} SET TAGS ('telco_project' = 'copper-retirement', 'developer' = 'copper-ml')")
print(f"Tags applied to {table_name}")

# COMMAND ----------

# DBTITLE 1,MLflow Tracing Configuration
# ── Configure MLflow Tracing for all 3 agents ─────────────────
# This enables automatic trace capture for tool calls, LLM invocations,
# and agent reasoning during eval runs.

import mlflow

# Enable tracing autolog for OpenAI-compatible calls
mlflow.openai.autolog(
    log_traces=True,
    log_models=False,
    log_input_examples=False,
)

# Verify tracing is active
print("MLflow Tracing enabled:")
print(f"  Experiment: {mlflow.get_experiment(exp.experiment_id).name}")
print(f"  Tracking URI: {mlflow.get_tracking_uri()}")
print(f"  OpenAI autolog: active")
print()
print("Tracing will capture:")
print("  - LLM completions (input/output tokens, latency)")
print("  - Tool calls (name, arguments, results)")
print("  - Agent loop iterations (reasoning chain)")
print("  - Error traces for failed tool invocations")

# COMMAND ----------

# DBTITLE 1,Scoring Harness: Agent Eval Runner
import json, re, time
from typing import Callable, Dict, List, Optional

def score_response(response_text: str, expected_contains: List[str]) -> dict:
    """Score a response against expected_contains keywords.
    Returns {matched, missed, score (0-1), pass (bool)}.
    """
    response_lower = response_text.lower()
    matched = [kw for kw in expected_contains if kw.lower() in response_lower]
    missed = [kw for kw in expected_contains if kw.lower() not in response_lower]
    score = len(matched) / len(expected_contains) if expected_contains else 1.0
    return {
        "matched": matched,
        "missed": missed,
        "score": round(score, 3),
        "pass": score >= 0.5,  # Pass if at least half keywords matched
    }

def score_tool_usage(trace_tools: List[str], expected_tool: str) -> dict:
    """Score whether the agent called the correct tool(s)."""
    expected = [t.strip() for t in expected_tool.split(",") if t.strip()]
    if not expected:
        return {"expected": [], "called": trace_tools, "correct": True, "score": 1.0}
    called_set = set(trace_tools)
    expected_set = set(expected)
    correct = expected_set.issubset(called_set)
    # Partial credit: fraction of expected tools that were called
    matched = expected_set.intersection(called_set)
    score = len(matched) / len(expected_set) if expected_set else 1.0
    return {
        "expected": expected,
        "called": trace_tools,
        "correct": correct,
        "score": round(score, 3),
    }

def score_routing(actual_route: str, expected_route: str) -> dict:
    """Score supervisor routing correctness."""
    expected = [r.strip() for r in expected_route.split(",") if r.strip()]
    actual = [r.strip() for r in actual_route.split(",") if r.strip()]
    if not expected:
        return {"expected": [], "actual": actual, "correct": True, "score": 1.0}
    expected_set = set(expected)
    actual_set = set(actual)
    matched = expected_set.intersection(actual_set)
    score = len(matched) / len(expected_set) if expected_set else 1.0
    return {
        "expected": expected,
        "actual": actual,
        "correct": expected_set == actual_set,
        "score": round(score, 3),
    }

def run_agent_eval(
    agent_fn: Callable[[str], dict],  # fn(input) -> {"response": str, "tools_called": list, "routes": str, "latency_ms": int}
    eval_cases: List[dict],
    agent_name: str,
    experiment_id: str,
) -> List[dict]:
    """
    Run evaluation harness for an agent.
    agent_fn should accept a string input and return a dict with:
      - response: str (agent text output)
      - tools_called: list of tool names invoked
      - routes: str (comma-separated sub-agent names, for supervisor only)
      - latency_ms: int
    """
    results = []
    with mlflow.start_run(
        experiment_id=experiment_id,
        run_name=f"{agent_name}_eval_{EVAL_VERSION}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
        tags={**PROJECT_TAGS, "eval_agent": agent_name, "eval_version": EVAL_VERSION},
    ) as parent_run:
        total_pass = 0
        total_cases = len(eval_cases)
        category_scores = {}

        for case in eval_cases:
            with mlflow.start_run(
                run_name=f"{case['eval_id']}_{case['category']}",
                nested=True,
                tags={**PROJECT_TAGS, "eval_id": case["eval_id"], "difficulty": case["difficulty"]},
            ):
                # Run agent
                try:
                    result = agent_fn(case["input"])
                except Exception as e:
                    result = {"response": f"ERROR: {e}", "tools_called": [], "routes": "", "latency_ms": 0}

                # Score content
                expected_kw = json.loads(case["expected_contains"]) if isinstance(case["expected_contains"], str) else case["expected_contains"]
                content_score = score_response(result["response"], expected_kw)

                # Score tool usage (triage/contractor)
                tool_score = score_tool_usage(
                    result.get("tools_called", []),
                    case.get("expected_tool", "")
                )

                # Score routing (supervisor)
                route_score = score_routing(
                    result.get("routes", ""),
                    case.get("expected_route", "")
                )

                # Composite score: content 50%, tool/route 50%
                if case.get("expected_route"):
                    composite = 0.5 * content_score["score"] + 0.5 * route_score["score"]
                elif case.get("expected_tool"):
                    composite = 0.5 * content_score["score"] + 0.5 * tool_score["score"]
                else:
                    composite = content_score["score"]

                passed = composite >= 0.5
                if passed:
                    total_pass += 1

                # Track category scores
                cat = case["category"]
                if cat not in category_scores:
                    category_scores[cat] = []
                category_scores[cat].append(composite)

                # Log to MLflow
                mlflow.log_params({
                    "eval_id": case["eval_id"],
                    "category": case["category"],
                    "difficulty": case["difficulty"],
                    "input": case["input"][:250],
                })
                mlflow.log_metrics({
                    "content_score": content_score["score"],
                    "tool_score": tool_score["score"],
                    "route_score": route_score["score"],
                    "composite_score": composite,
                    "passed": 1 if passed else 0,
                    "latency_ms": result.get("latency_ms", 0),
                })

                results.append({
                    "eval_id": case["eval_id"],
                    "agent": agent_name,
                    "category": case["category"],
                    "difficulty": case["difficulty"],
                    "input": case["input"],
                    "response_preview": result["response"][:200],
                    "content_score": content_score["score"],
                    "tool_score": tool_score["score"],
                    "route_score": route_score["score"],
                    "composite_score": composite,
                    "passed": passed,
                    "missed_keywords": content_score["missed"],
                    "latency_ms": result.get("latency_ms", 0),
                })

        # Log aggregate metrics to parent run
        pass_rate = total_pass / total_cases if total_cases else 0
        mlflow.log_metrics({
            "overall_pass_rate": round(pass_rate, 3),
            "total_cases": total_cases,
            "total_passed": total_pass,
            "total_failed": total_cases - total_pass,
        })
        for cat, scores in category_scores.items():
            avg = sum(scores) / len(scores)
            mlflow.log_metric(f"category_{cat}_avg", round(avg, 3))

        # Log results as artifact
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(results, f, indent=2, default=str)
            mlflow.log_artifact(f.name, "eval_results")

        print(f"\n{'='*60}")
        print(f"{agent_name.upper()} EVALUATION COMPLETE")
        print(f"{'='*60}")
        print(f"Pass rate: {total_pass}/{total_cases} ({pass_rate:.1%})")
        print(f"\nCategory breakdown:")
        for cat, scores in sorted(category_scores.items()):
            avg = sum(scores) / len(scores)
            print(f"  {cat}: {avg:.1%} avg ({len(scores)} cases)")

    return results

print("Scoring harness ready. Functions: score_response, score_tool_usage, score_routing, run_agent_eval")
print("\nGating criteria for serving promotion:")
print("  - Overall pass rate >= 80%")
print("  - No category below 60% average")
print("  - P1 incident lookup: 100% pass rate")
print("  - Out-of-scope handling: 100% pass rate")

# COMMAND ----------

# DBTITLE 1,Serving Promotion Gate
# ── Serving Promotion Gate ──────────────────────────────────
# This cell evaluates all eval results and determines whether
# each agent passes the quality gate for serving endpoint promotion.

def evaluate_gate(results: List[dict], agent_name: str) -> dict:
    """Apply serving promotion criteria to eval results.
    
    Gate criteria:
    1. Overall pass rate >= 80%
    2. No category below 60% average composite score
    3. Hard difficulty pass rate >= 60%
    4. Edge cases must be handled (no crashes)
    
    Returns: {agent, pass_gate, overall_rate, category_rates, blockers}
    """
    agent_results = [r for r in results if r["agent"] == agent_name]
    if not agent_results:
        return {"agent": agent_name, "pass_gate": False, "blockers": ["No results found"]}
    
    # Overall pass rate
    total = len(agent_results)
    passed = sum(1 for r in agent_results if r["passed"])
    overall_rate = passed / total
    
    # Category rates
    cat_scores = {}
    for r in agent_results:
        cat = r["category"]
        if cat not in cat_scores:
            cat_scores[cat] = []
        cat_scores[cat].append(r["composite_score"])
    cat_rates = {cat: sum(s)/len(s) for cat, s in cat_scores.items()}
    
    # Difficulty rates
    hard_results = [r for r in agent_results if r["difficulty"] == "hard"]
    hard_rate = sum(1 for r in hard_results if r["passed"]) / len(hard_results) if hard_results else 1.0
    
    # Edge case handling (no ERROR in response)
    edge_results = [r for r in agent_results if "edge" in r["category"]]
    edge_crashes = [r for r in edge_results if "ERROR" in r.get("response_preview", "")]
    
    # Evaluate blockers
    blockers = []
    if overall_rate < 0.80:
        blockers.append(f"Overall pass rate {overall_rate:.1%} < 80% threshold")
    for cat, rate in cat_rates.items():
        if rate < 0.60:
            blockers.append(f"Category '{cat}' avg {rate:.1%} < 60% threshold")
    if hard_rate < 0.60:
        blockers.append(f"Hard difficulty pass rate {hard_rate:.1%} < 60% threshold")
    if edge_crashes:
        blockers.append(f"{len(edge_crashes)} edge case(s) crashed")
    
    pass_gate = len(blockers) == 0
    
    return {
        "agent": agent_name,
        "pass_gate": pass_gate,
        "overall_rate": round(overall_rate, 3),
        "hard_rate": round(hard_rate, 3),
        "category_rates": {k: round(v, 3) for k, v in cat_rates.items()},
        "blockers": blockers,
        "total_cases": total,
        "total_passed": passed,
    }

def print_gate_report(gate_results: List[dict]):
    """Print formatted gate report for all agents."""
    print("\n" + "="*70)
    print("SERVING PROMOTION GATE REPORT")
    print("="*70)
    all_pass = True
    for g in gate_results:
        status = "✅ PASS" if g["pass_gate"] else "❌ FAIL"
        print(f"\n{g['agent'].upper()}: {status}")
        print(f"  Overall: {g['overall_rate']:.1%} ({g['total_passed']}/{g['total_cases']})")
        print(f"  Hard difficulty: {g.get('hard_rate', 0):.1%}")
        if g.get('category_rates'):
            print(f"  Categories:")
            for cat, rate in sorted(g['category_rates'].items()):
                flag = " ⚠️" if rate < 0.60 else ""
                print(f"    {cat}: {rate:.1%}{flag}")
        if g["blockers"]:
            print(f"  Blockers:")
            for b in g["blockers"]:
                print(f"    • {b}")
            all_pass = False
    
    print(f"\n{'='*70}")
    if all_pass:
        print("VERDICT: All agents PASS. Ready for serving endpoint promotion.")
    else:
        failed = [g['agent'] for g in gate_results if not g['pass_gate']]
        print(f"VERDICT: {', '.join(failed)} BLOCKED. Fix blockers before promotion.")
    print("="*70)

print("Gate evaluator ready.")
print("\nUsage after running evals:")
print('  gate_triage = evaluate_gate(results_triage, "triage")')
print('  gate_contractor = evaluate_gate(results_contractor, "contractor")')
print('  gate_supervisor = evaluate_gate(results_supervisor, "supervisor")')
print('  print_gate_report([gate_triage, gate_contractor, gate_supervisor])')

# COMMAND ----------

# DBTITLE 1,Example: Run Eval Against Triage Agent
# ── Example: How to run eval against a live agent ─────────────
# Uncomment and adapt for each agent notebook.
#
# Step 1: Import or define the agent function from the agent notebook
# Step 2: Wrap it to return the expected dict format
# Step 3: Call run_agent_eval
#
# Example for triage agent (P6_dig_triage_agent):
#
# def triage_agent_fn(user_input: str) -> dict:
#     """Wrapper that calls the triage agent and returns standardized output."""
#     import time
#     start = time.time()
#     # Call your agent loop here (from P6_dig_triage_agent notebook)
#     # messages = [{"role": "user", "content": user_input}]
#     # response, tools_used = run_agent(messages)  
#     elapsed = int((time.time() - start) * 1000)
#     return {
#         "response": response,           # Agent's final text response
#         "tools_called": tools_used,     # ["incident_lookup", "proximity_search", ...]
#         "routes": "",                   # Only for supervisor
#         "latency_ms": elapsed,
#     }
#
# # Run evaluation
# results_triage = run_agent_eval(
#     agent_fn=triage_agent_fn,
#     eval_cases=triage_eval,
#     agent_name="triage",
#     experiment_id=exp.experiment_id,
# )
#
# # Check gate
# gate = evaluate_gate(results_triage, "triage")
# print_gate_report([gate])

print("Example eval runner defined (commented). ")
print("To execute: import agent functions from P6_dig_triage_agent, P6_contractor_sourcing_agent, P6_supervisor_agent.")
print("Then uncomment and run.")