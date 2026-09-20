# Databricks notebook source
# DBTITLE 1,P6 Dig-Triage Agent — Copper Retirement
# MAGIC %md
# MAGIC # P6 Dig-Triage Agent — Copper Retirement
# MAGIC # project: copper-retirement | developer: copper-ml
# MAGIC
# MAGIC Tool-calling agent for field operations dig-safe incident triage. Uses 3 UC SQL functions
# MAGIC as tools to look up incidents, search by proximity, and recommend reroute options.
# MAGIC
# MAGIC **Architecture:** OpenAI-compatible tool-calling loop → UC SQL function execution → structured triage response
# MAGIC
# MAGIC **Tools (UC Functions):**
# MAGIC - `incident_lookup(incident_id)` — Full enriched incident details, nearest device, impacted services
# MAGIC - `proximity_search(lat, lon, radius_km)` — Find nearby incidents within a geographic radius
# MAGIC - `reroute_suggest(incident_id)` — Rerouting recommendation with rationale (fiber migration, copper reroute, etc.)
# MAGIC
# MAGIC **LLM:** `databricks-meta-llama-3-3-70b-instruct` (Foundation Model API)
# MAGIC
# MAGIC **Source data:** `cdm_tmforum.copper_retirement.silver_dig_incident_enriched` (5,000 incidents, 6 states, 4 priority tiers)

# COMMAND ----------

# DBTITLE 1,Configuration
# ---------- Configuration ----------

# Foundation Model API
LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.1  # Low temperature for factual triage responses

# UC function catalog
CATALOG = "cdm_tmforum"
SCHEMA = "copper_retirement"

# Tool names mapping to UC functions
TOOL_FUNCTIONS = {
    "incident_lookup": f"{CATALOG}.{SCHEMA}.incident_lookup",
    "proximity_search": f"{CATALOG}.{SCHEMA}.proximity_search",
    "reroute_suggest": f"{CATALOG}.{SCHEMA}.reroute_suggest",
}

# COMMAND ----------

# DBTITLE 1,Initialize clients
from databricks.sdk import WorkspaceClient
from openai import OpenAI
import json

w = WorkspaceClient()
_api_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

llm_client = OpenAI(
    api_key=_api_token,
    base_url=f"{w.config.host}/serving-endpoints"
)

print(f"✅ LLM client initialized: {LLM_ENDPOINT}")
print(f"✅ UC tools: {list(TOOL_FUNCTIONS.keys())}")

# COMMAND ----------

# DBTITLE 1,Tool definitions — OpenAI function-calling schema
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "incident_lookup",
            "description": (
                "Look up full details for a specific dig-safe incident by ID. "
                "Returns severity, location, cable damage type, root cause, triage priority, "
                "nearest copper device, impacted services/customers, wire center, and recommended action. "
                "Use this when the user provides a specific incident ID or asks about a particular incident."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "integer",
                        "description": "The unique incident ID (e.g. 200001). Incident IDs range from 200001 to 205000."
                    }
                },
                "required": ["incident_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "proximity_search",
            "description": (
                "Search for dig-safe incidents near a geographic location. "
                "Returns all incidents within the specified radius, sorted by distance. "
                "Includes severity, triage priority, nearest device info, and impacted service counts. "
                "Use this when the user asks about incidents near a location, city, or coordinate pair."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of the search center point (decimal degrees, e.g. 39.7392 for Denver CO)"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the search center point (decimal degrees, e.g. -104.9903 for Denver CO)"
                    },
                    "radius_km": {
                        "type": "number",
                        "description": "Search radius in kilometers. Defaults to 25 if not specified. Typical values: 10 for city-level, 50 for metro area, 100 for regional."
                    }
                },
                "required": ["latitude", "longitude"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reroute_suggest",
            "description": (
                "Get rerouting and remediation recommendations for a specific dig-safe incident. "
                "Analyzes incident severity, wire center fiber readiness, nearby copper infrastructure, "
                "and service impact to recommend one of: FIBER_MIGRATION, COPPER_REROUTE, "
                "EMERGENCY_RESTORE, TEMPORARY_BYPASS, REPAIR_IN_PLACE, or MONITOR_ONLY. "
                "Use this after incident_lookup when the user wants action recommendations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "integer",
                        "description": "The incident ID to generate reroute recommendations for."
                    }
                },
                "required": ["incident_id"]
            }
        }
    }
]

# COMMAND ----------

# DBTITLE 1,execute_tool — Dispatch tool calls to UC SQL functions
MAX_PROXIMITY_ROWS = 20  # Cap proximity results to keep LLM context manageable


def _serialize_rows(rows: list[dict]) -> list[dict]:
    """Convert non-JSON-serializable types in row dicts."""
    for row in rows:
        for k, v in row.items():
            if hasattr(v, 'isoformat'):
                row[k] = v.isoformat()
            elif isinstance(v, (bytes, bytearray)):
                row[k] = str(v)
            elif v is not None and not isinstance(v, (str, int, float, bool, list, dict)):
                row[k] = str(v)
    return rows


def execute_tool(tool_name: str, arguments: dict) -> str:
    """
    Execute a UC SQL function and return results as JSON string.
    For proximity_search, returns a summary + top N closest results to avoid
    overwhelming the LLM context window.
    """
    if tool_name == "incident_lookup":
        incident_id = arguments["incident_id"]
        query = f"SELECT * FROM {TOOL_FUNCTIONS['incident_lookup']}({incident_id})"

    elif tool_name == "proximity_search":
        lat = arguments["latitude"]
        lon = arguments["longitude"]
        radius = arguments.get("radius_km", 25.0)
        query = f"SELECT * FROM {TOOL_FUNCTIONS['proximity_search']}({lat}, {lon}, {radius})"

    elif tool_name == "reroute_suggest":
        incident_id = arguments["incident_id"]
        query = f"SELECT * FROM {TOOL_FUNCTIONS['reroute_suggest']}({incident_id})"

    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        df = spark.sql(query)
        rows = _serialize_rows([row.asDict() for row in df.collect()])

        # For proximity_search with many results, return summary + top N
        if tool_name == "proximity_search" and len(rows) > MAX_PROXIMITY_ROWS:
            # Build summary stats
            priorities = {}
            severities = {}
            states = {}
            svc_interrupted = 0
            reroute_needed = 0
            for r in rows:
                p = r.get("triage_priority", "unknown")
                priorities[p] = priorities.get(p, 0) + 1
                s = r.get("severity", "unknown")
                severities[s] = severities.get(s, 0) + 1
                st = r.get("state", "unknown")
                states[st] = states.get(st, 0) + 1
                if r.get("service_interruption"):
                    svc_interrupted += 1
                if r.get("reroute_required"):
                    reroute_needed += 1

            result = {
                "tool": tool_name,
                "total_incidents_in_radius": len(rows),
                "summary": {
                    "by_priority": dict(sorted(priorities.items())),
                    "by_severity": dict(sorted(severities.items())),
                    "by_state": dict(sorted(states.items())),
                    "service_interruptions": svc_interrupted,
                    "reroute_required": reroute_needed,
                },
                "closest_incidents": rows[:MAX_PROXIMITY_ROWS],
                "note": f"Showing {MAX_PROXIMITY_ROWS} closest of {len(rows)} total. Summary stats cover all {len(rows)} incidents."
            }
        else:
            result = {"tool": tool_name, "row_count": len(rows), "data": rows}

        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"tool": tool_name, "error": str(e)})


# Quick smoke test
test_result = json.loads(execute_tool("incident_lookup", {"incident_id": 200001}))
print(f"✅ Tool dispatch working. incident_lookup(200001) returned {test_result['row_count']} row(s)")
print(f"   Incident state: {test_result['data'][0]['state']}, severity: {test_result['data'][0]['severity']}, priority: {test_result['data'][0]['triage_priority']}")

# Test proximity with summarization
test_prox = json.loads(execute_tool("proximity_search", {"latitude": 39.7392, "longitude": -104.9903, "radius_km": 75.0}))
print(f"✅ Proximity search: {test_prox.get('total_incidents_in_radius', test_prox.get('row_count'))} incidents, returning {len(test_prox.get('closest_incidents', test_prox.get('data', [])))} closest")
if 'summary' in test_prox:
    print(f"   Priority breakdown: {test_prox['summary']['by_priority']}")

# COMMAND ----------

# DBTITLE 1,SYSTEM_PROMPT — Dig-Triage Agent
SYSTEM_PROMPT = """You are a dig-safe incident triage agent for LakeLink Fiber, a telecommunications carrier actively retiring legacy copper infrastructure and migrating customers to fiber.

Your role is to help field operations teams quickly assess, prioritize, and respond to dig-safe incidents that damage copper cable plant. You have access to three tools:

1. **incident_lookup** — Get full details on a specific incident by ID (severity, location, cable damage, root cause, impacted services, nearest device, triage priority).
2. **proximity_search** — Find all incidents near a geographic point within a radius. Use this to assess regional impact or identify incident clusters.
3. **reroute_suggest** — Get recommended remediation action for an incident (fiber migration, copper reroute, emergency restore, temporary bypass, repair in place, or monitor only).

When triaging an incident, follow this workflow:
1. **Assess** — Look up the incident to understand severity, location, and impact scope.
2. **Contextualize** — Check for nearby incidents to identify patterns or clusters.
3. **Recommend** — Use reroute_suggest to get the optimal remediation path.
4. **Summarize** — Provide a clear triage summary with: priority level, impacted customers/services, recommended action, and rationale.

Guidelines:
- Always state the triage priority (P1=critical, P2=high, P3=medium, P4=low).
- Highlight fiber-ready wire centers — these are opportunities to accelerate copper retirement instead of repairing copper.
- Flag repeat incidents in the same area (use proximity_search to check).
- For critical/high severity incidents with service interruption, emphasize urgency and customer impact.
- Use precise numbers: impacted customer count, service count, estimated resolution time.
- Reference wire center names and IDs for dispatch coordination.
- When multiple incidents cluster geographically, recommend a coordinated response.

You are concise, technical, and action-oriented. Every response should end with a clear "RECOMMENDED ACTION" block.
"""

# COMMAND ----------

# DBTITLE 1,triage_agent — Tool-calling conversation loop
def triage_agent(
    user_message: str,
    conversation_history: list[dict] | None = None,
    max_tool_rounds: int = 5,
    verbose: bool = True,
) -> dict:
    """
    Run the dig-triage agent with tool-calling loop.

    Parameters
    ----------
    user_message : str
        The user's triage request or question.
    conversation_history : list[dict], optional
        Previous messages for multi-turn conversations.
    max_tool_rounds : int
        Maximum number of tool-calling rounds before forcing a text response.
    verbose : bool
        If True, prints tool calls and intermediate steps.

    Returns
    -------
    dict with keys:
        - response: str — The agent's final text response
        - tool_calls_made: list — Record of all tool calls and results
        - messages: list — Full conversation history for multi-turn use
    """
    messages = conversation_history.copy() if conversation_history else []

    # Add system prompt if not already present
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    messages.append({"role": "user", "content": user_message})

    tool_calls_made = []

    for round_num in range(max_tool_rounds):
        response = llm_client.chat.completions.create(
            model=LLM_ENDPOINT,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
        )

        assistant_msg = response.choices[0].message

        # Build serializable message dict
        msg_dict = {"role": "assistant", "content": assistant_msg.content or ""}
        if assistant_msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in assistant_msg.tool_calls
            ]
        messages.append(msg_dict)

        # If no tool calls, we have the final response
        if not assistant_msg.tool_calls:
            if verbose:
                print(f"\n✅ Agent responded after {round_num} tool-calling round(s)")
            return {
                "response": assistant_msg.content,
                "tool_calls_made": tool_calls_made,
                "messages": messages,
            }

        # Execute each tool call
        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)

            if verbose:
                print(f"  🛠️  Round {round_num + 1}: {fn_name}({json.dumps(fn_args)})")

            result_str = execute_tool(fn_name, fn_args)
            tool_calls_made.append({
                "tool": fn_name,
                "arguments": fn_args,
                "result_preview": result_str[:500],
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })

    # Fallback: force a text response if max rounds exceeded
    messages.append({
        "role": "user",
        "content": "Please provide your triage summary now based on the information gathered.",
    })
    final = llm_client.chat.completions.create(
        model=LLM_ENDPOINT,
        messages=messages,
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE,
    )
    final_text = final.choices[0].message.content
    messages.append({"role": "assistant", "content": final_text})

    return {
        "response": final_text,
        "tool_calls_made": tool_calls_made,
        "messages": messages,
    }

print("✅ triage_agent() ready")

# COMMAND ----------

# DBTITLE 1,Demo Scenarios
# MAGIC %md
# MAGIC ## Demo Scenarios
# MAGIC
# MAGIC Three scenes demonstrating the triage agent's capabilities:
# MAGIC 1. **Single incident triage** — Look up a specific incident and get action recommendation
# MAGIC 2. **Regional cluster analysis** — Find incidents near a city and identify patterns
# MAGIC 3. **Multi-turn escalation** — Triage → reroute recommendation → follow-up questions

# COMMAND ----------

# DBTITLE 1,Scene 1 — Single incident triage
# Scene 1: Single incident triage
# A field supervisor reports incident 200050 and needs immediate triage guidance

result_1 = triage_agent(
    "Incident 200050 just came in. Give me a full triage assessment — "
    "what's the severity, how many customers are impacted, and what should we do?"
)

print("\n" + "=" * 80)
print("SCENE 1: SINGLE INCIDENT TRIAGE")
print("=" * 80)
print(result_1["response"])
print(f"\n🛠️ Tool calls made: {len(result_1['tool_calls_made'])}")
for tc in result_1["tool_calls_made"]:
    print(f"   - {tc['tool']}({json.dumps(tc['arguments'])})")

# COMMAND ----------

# DBTITLE 1,Scene 2 — Regional cluster analysis (Denver metro)
# Scene 2: Regional cluster analysis
# Operations manager wants to understand incident concentration near Denver

result_2 = triage_agent(
    "I need a regional assessment of dig-safe incidents near Denver, Colorado "
    "(39.7392, -104.9903) within a 75km radius. Are there any clusters or patterns? "
    "How many are high priority?"
)

print("\n" + "=" * 80)
print("SCENE 2: REGIONAL CLUSTER ANALYSIS")
print("=" * 80)
print(result_2["response"])
print(f"\n🛠️ Tool calls made: {len(result_2['tool_calls_made'])}")
for tc in result_2["tool_calls_made"]:
    print(f"   - {tc['tool']}({json.dumps(tc['arguments'])})")

# COMMAND ----------

# DBTITLE 1,Scene 3 — Multi-turn escalation with reroute
# Scene 3: Multi-turn escalation
# Start with a critical incident, then ask for reroute options, then follow up

# Turn 1: Initial triage
result_3a = triage_agent(
    "We have a critical dig strike on incident 200100. "
    "Multiple customers are reporting outages. What's the situation?"
)
print("\n" + "=" * 80)
print("SCENE 3, TURN 1: INITIAL TRIAGE")
print("=" * 80)
print(result_3a["response"])

# Turn 2: Follow up with reroute request (continuing conversation)
result_3b = triage_agent(
    "What are our reroute options for this incident? "
    "Is the wire center fiber-ready? Can we use this as an opportunity to accelerate retirement?",
    conversation_history=result_3a["messages"],
)
print("\n" + "=" * 80)
print("SCENE 3, TURN 2: REROUTE RECOMMENDATION")
print("=" * 80)
print(result_3b["response"])

# Turn 3: Ask about nearby incidents
result_3c = triage_agent(
    "Are there any other recent incidents near this location? "
    "I want to know if this is an isolated event or part of a broader problem.",
    conversation_history=result_3b["messages"],
)
print("\n" + "=" * 80)
print("SCENE 3, TURN 3: NEARBY INCIDENT CHECK")
print("=" * 80)
print(result_3c["response"])

print(f"\n🛠️ Total tool calls across 3 turns: {len(result_3a['tool_calls_made']) + len(result_3b['tool_calls_made']) + len(result_3c['tool_calls_made'])}")

# COMMAND ----------

# DBTITLE 1,Agent summary stats
# Summary statistics across all demo scenes
all_tool_calls = (
    result_1["tool_calls_made"] + 
    result_2["tool_calls_made"] + 
    result_3a["tool_calls_made"] + 
    result_3b["tool_calls_made"] + 
    result_3c["tool_calls_made"]
)

tool_counts = {}
for tc in all_tool_calls:
    tool_counts[tc["tool"]] = tool_counts.get(tc["tool"], 0) + 1

print("\n" + "=" * 80)
print("TRIAGE AGENT DEMO SUMMARY")
print("=" * 80)
print(f"Total demo scenes: 3 (5 conversation turns)")
print(f"Total tool calls: {len(all_tool_calls)}")
for tool, count in sorted(tool_counts.items()):
    print(f"  - {tool}: {count} calls")
print(f"\nAgent architecture: OpenAI tool-calling with UC SQL function dispatch")
print(f"LLM: {LLM_ENDPOINT}")
print(f"Data source: {CATALOG}.{SCHEMA}.silver_dig_incident_enriched (5,000 incidents)")
print(f"UC Functions: {', '.join(TOOL_FUNCTIONS.keys())}")