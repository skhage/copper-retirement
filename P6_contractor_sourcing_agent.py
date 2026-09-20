# Databricks notebook source
# DBTITLE 1,P6 Contractor Sourcing Agent — Copper Retirement
# MAGIC %md
# MAGIC # P6 Contractor Sourcing Agent — Copper Retirement
# MAGIC # project: copper-retirement | developer: copper-ml
# MAGIC
# MAGIC Tool-calling agent for contractor selection and dispatch planning.
# MAGIC Queries 4 contractor tables to search, rank, and recommend contractors for copper retirement waves.
# MAGIC
# MAGIC **Architecture:** OpenAI tool-calling loop → Spark SQL execution → ranked contractor shortlists
# MAGIC
# MAGIC **Tools (SQL queries against UC tables):**
# MAGIC - `search_contractors(state, type, min_safety_score)` — Search gold_contractor_scorecard by state/type/safety
# MAGIC - `contractor_incidents(contractor_name)` — Incident history + fault rate from contractor_incident_history
# MAGIC - `wave_assignments(wave, state)` — Current assignments from gold_contractor_assignment_plan
# MAGIC
# MAGIC **Data:**
# MAGIC - `gold_contractor_scorecard` (10K) — Full contractor registry with scores
# MAGIC - `contractor_incident_history` (3.9K) — Dig-safe incident records per contractor
# MAGIC - `gold_contractor_assignment_plan` (35) — Optimized wave×state assignments
# MAGIC - `contractor_performance` (10K) — Raw performance metrics

# COMMAND ----------

# DBTITLE 1,Configuration + clients
from databricks.sdk import WorkspaceClient
from openai import OpenAI
import json

# ---------- Configuration ----------
LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.1
CATALOG = "cdm_tmforum"
SCHEMA = "copper_retirement"
MAX_SEARCH_ROWS = 15  # Cap contractor search results for LLM context

# ---------- Initialize ----------
w = WorkspaceClient()
_api_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
llm_client = OpenAI(api_key=_api_token, base_url=f"{w.config.host}/serving-endpoints")
print(f"✅ LLM: {LLM_ENDPOINT} | Data: {CATALOG}.{SCHEMA}")

# COMMAND ----------

# DBTITLE 1,Tool definitions — contractor sourcing schema
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_contractors",
            "description": (
                "Search the contractor registry for contractors matching given criteria. "
                "Returns ranked list by composite score (safety 40% + rating 30% + SLA 30%). "
                "Can filter by state, contractor type, minimum safety score, and certification status. "
                "Use this to find qualified contractors for a copper retirement wave."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "description": "US state code to filter by (e.g. 'CO', 'OR', 'AZ'). Matches primary_state."
                    },
                    "contractor_type": {
                        "type": "string",
                        "description": "Contractor specialization: general_construction, underground_boring, aerial_line, multi_discipline, fiber_splicing, utility_locator"
                    },
                    "min_safety_score": {
                        "type": "number",
                        "description": "Minimum safety score (0-100). Preferred contractors have >= 80. Default 70."
                    },
                    "certified_only": {
                        "type": "boolean",
                        "description": "If true, only return certified contractors. Default true."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "contractor_incidents",
            "description": (
                "Get dig-safe incident history for a specific contractor. "
                "Returns fault rate, total incidents, at-fault count, severity breakdown, "
                "and compliance score. Use this to vet a contractor before assignment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "contractor_name": {
                        "type": "string",
                        "description": "Name of the contractor (exact or partial match)."
                    }
                },
                "required": ["contractor_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wave_assignments",
            "description": (
                "Get current contractor assignments for a specific retirement wave and/or state. "
                "Shows which contractors are already allocated, their crew-days, costs, and composite scores. "
                "Use this to understand existing capacity before recommending additional contractors."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "wave": {
                        "type": "string",
                        "description": "Retirement wave (e.g. '2026-Q3', '2027-Q1'). Optional."
                    },
                    "state": {
                        "type": "string",
                        "description": "US state code (e.g. 'CO'). Optional."
                    }
                },
                "required": []
            }
        }
    }
]

# COMMAND ----------

# DBTITLE 1,execute_tool — SQL-based contractor tool dispatch
_STATE_CODES = {"alabama":"AL","alaska":"AK","arizona":"AZ","arkansas":"AR","california":"CA","colorado":"CO","connecticut":"CT","delaware":"DE","florida":"FL","georgia":"GA","hawaii":"HI","idaho":"ID","illinois":"IL","indiana":"IN","iowa":"IA","kansas":"KS","kentucky":"KY","louisiana":"LA","maine":"ME","maryland":"MD","massachusetts":"MA","michigan":"MI","minnesota":"MN","mississippi":"MS","missouri":"MO","montana":"MT","nebraska":"NE","nevada":"NV","new hampshire":"NH","new jersey":"NJ","new mexico":"NM","new york":"NY","north carolina":"NC","north dakota":"ND","ohio":"OH","oklahoma":"OK","oregon":"OR","pennsylvania":"PA","rhode island":"RI","south carolina":"SC","south dakota":"SD","tennessee":"TN","texas":"TX","utah":"UT","vermont":"VT","virginia":"VA","washington":"WA","west virginia":"WV","wisconsin":"WI","wyoming":"WY"}
def _norm_state(s):
    if not s: return s
    return _STATE_CODES.get(s.strip().lower(), s.strip().upper()[:2])
def _norm_type(t):
    if not t: return t
    return t.strip().lower().replace(" ", "_")

def _serialize_rows(rows):
    for row in rows:
        for k, v in row.items():
            if hasattr(v, 'isoformat'): row[k] = v.isoformat()
            elif v is not None and not isinstance(v, (str, int, float, bool, list, dict)): row[k] = str(v)
    return rows


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute contractor sourcing tools via Spark SQL."""
    try:
        if tool_name == "search_contractors":
            conditions = ["1=1"]
            if arguments.get("state"):
                conditions.append(f"primary_state = '{_norm_state(arguments['state'])}'")
            if arguments.get("contractor_type"):
                conditions.append(f"contractor_type = '{_norm_type(arguments['contractor_type'])}'")
            min_safety = arguments.get("min_safety_score", 70)
            conditions.append(f"safety_score >= {min_safety}")
            if arguments.get("certified_only", True):
                conditions.append("certification_status = 'fully_certified'")
            where = " AND ".join(conditions)
            query = f"""
                SELECT contractor_performance_id, contractor_name, contractor_type,
                       primary_state, certification_status, dispatch_status,
                       crew_size, CAST(safety_score AS DOUBLE) AS safety_score,
                       CAST(overall_rating AS DOUBLE) AS overall_rating,
                       CAST(sla_compliance_pct AS DOUBLE) AS sla_compliance_pct,
                       ROUND((CAST(safety_score AS DOUBLE)/100.0)*0.4 + (CAST(overall_rating AS DOUBLE)/5.0)*0.3 + (CAST(sla_compliance_pct AS DOUBLE)/100.0)*0.3, 4) AS composite_score,
                       active_project_count, years_in_business,
                       CAST(osha_recordable_rate AS DOUBLE) AS osha_recordable_rate
                FROM {CATALOG}.{SCHEMA}.gold_contractor_scorecard
                WHERE {where}
                ORDER BY composite_score DESC
            """
            df = spark.sql(query)
            all_rows = _serialize_rows([r.asDict() for r in df.collect()])
            if len(all_rows) > MAX_SEARCH_ROWS:
                return json.dumps({
                    "tool": tool_name, "total_matching": len(all_rows),
                    "top_contractors": all_rows[:MAX_SEARCH_ROWS],
                    "note": f"Showing top {MAX_SEARCH_ROWS} of {len(all_rows)} by composite score."
                }, default=str)
            return json.dumps({"tool": tool_name, "row_count": len(all_rows), "data": all_rows}, default=str)

        elif tool_name == "contractor_incidents":
            name = arguments["contractor_name"].replace("'", "''")
            query = f"""
                SELECT contractor_name, contractor_type, primary_state,
                       CAST(rolling_12m_fault_rate AS DOUBLE) AS rolling_12m_fault_rate,
                       CAST(compliance_score AS DOUBLE) AS compliance_score,
                       total_incident_count, total_at_fault_count,
                       incidents_last_12m, at_fault_last_12m,
                       severe_incident_count, service_interruption_count,
                       CAST(avg_repair_cost AS DOUBLE) AS avg_repair_cost,
                       CAST(avg_resolution_hours AS DOUBLE) AS avg_resolution_hours,
                       certification_status,
                       CAST(contractor_safety_score AS DOUBLE) AS safety_score,
                       CAST(contractor_overall_rating AS DOUBLE) AS overall_rating,
                       years_in_business,
                       first_incident_date, last_incident_date
                FROM {CATALOG}.{SCHEMA}.contractor_incident_history
                WHERE contractor_name ILIKE '%{name}%'
            """
            rows = _serialize_rows([r.asDict() for r in spark.sql(query).collect()])
            return json.dumps({"tool": tool_name, "row_count": len(rows), "data": rows}, default=str)

        elif tool_name == "wave_assignments":
            conditions = ["1=1"]
            if arguments.get("wave"):
                conditions.append(f"wave = '{arguments['wave']}'")
            if arguments.get("state"):
                conditions.append(f"state_code = '{_norm_state(arguments['state'])}'")
            where = " AND ".join(conditions)
            query = f"""
                SELECT wave, state_code, contractor_name, contractor_type,
                       composite_score, allocated_crew_days, estimated_cost_usd,
                       crew_size, safety_score, sla_compliance_pct,
                       wire_centers_in_wave, devices_in_wave
                FROM {CATALOG}.{SCHEMA}.gold_contractor_assignment_plan
                WHERE {where}
                ORDER BY composite_score DESC
            """
            rows = _serialize_rows([r.asDict() for r in spark.sql(query).collect()])
            return json.dumps({"tool": tool_name, "row_count": len(rows), "data": rows}, default=str)

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"tool": tool_name, "error": str(e)})


# Smoke tests
t1 = json.loads(execute_tool("search_contractors", {"state": "CO", "min_safety_score": 90}))
print(f"✅ search_contractors(CO, safety>=90): {t1.get('total_matching', t1.get('row_count'))} contractors")

t2 = json.loads(execute_tool("wave_assignments", {"wave": "2026-Q3"}))
print(f"✅ wave_assignments(2026-Q3): {t2['row_count']} assignments")

t3 = json.loads(execute_tool("contractor_incidents", {"contractor_name": "Prairie Fiber"}))
print(f"✅ contractor_incidents(Prairie Fiber): {t3['row_count']} records")

# COMMAND ----------

# DBTITLE 1,SYSTEM_PROMPT — Contractor Sourcing Agent
SYSTEM_PROMPT = """You are a contractor sourcing agent for LakeLink Fiber's copper retirement program.

Your role is to help project managers find, evaluate, and recommend contractors for copper retirement field work — cable removal, fiber installation, aerial line work, and underground boring. You have three tools:

1. **search_contractors** — Search the contractor registry by state, type, safety score, and certification. Returns ranked list by composite score.
2. **contractor_incidents** — Get dig-safe incident history and fault rate for a specific contractor. Use to vet candidates.
3. **wave_assignments** — See which contractors are already assigned to a retirement wave/state. Use to check existing capacity.

When sourcing contractors:
1. **Understand the need** — Which wave, state, contractor type is needed?
2. **Search candidates** — Filter by state proximity, type, and minimum safety (preferred = 80+).
3. **Vet top candidates** — Check incident history and fault rates for the top 3-5.
4. **Check existing assignments** — See what's already allocated to avoid over-committing.
5. **Recommend a shortlist** — Ranked by composite score with pros/cons for each.

Guidelines:
- Always flag contractors with fault_rate > 10% or safety_score < 80 as risk factors.
- Prefer contractors already dispatched as 'preferred' status.
- Note certification status — only 'certified' contractors are eligible.
- Consider crew_size relative to the wave's device count and wire center count.
- Highlight any contractor with revoked certification or high OSHA rates.
- Present recommendations in a clear ranked table format.

Be concise, data-driven, and always end with a RECOMMENDED SHORTLIST.
"""

# COMMAND ----------

# DBTITLE 1,contractor_agent — Tool-calling conversation loop
def contractor_agent(
    user_message: str,
    conversation_history: list[dict] | None = None,
    max_tool_rounds: int = 5,
    verbose: bool = True,
) -> dict:
    """Run the contractor sourcing agent with tool-calling loop."""
    messages = conversation_history.copy() if conversation_history else []
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": user_message})
    tool_calls_made = []

    for round_num in range(max_tool_rounds):
        response = llm_client.chat.completions.create(
            model=LLM_ENDPOINT, messages=messages, tools=TOOLS,
            tool_choice="auto", max_tokens=LLM_MAX_TOKENS, temperature=LLM_TEMPERATURE
        )
        amsg = response.choices[0].message
        md = {"role": "assistant", "content": amsg.content or ""}
        if amsg.tool_calls:
            md["tool_calls"] = [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in amsg.tool_calls
            ]
        messages.append(md)

        if not amsg.tool_calls:
            if verbose:
                print(f"\n✅ Agent responded after {round_num} tool-calling round(s)")
            return {"response": amsg.content, "tool_calls_made": tool_calls_made, "messages": messages}

        for tc in amsg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            if verbose:
                print(f"  🛠️  Round {round_num+1}: {fn_name}({json.dumps(fn_args)})")
            result_str = execute_tool(fn_name, fn_args)
            tool_calls_made.append({"tool": fn_name, "arguments": fn_args})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})

    # Fallback
    messages.append({"role": "user", "content": "Please provide your contractor recommendation now."})
    final = llm_client.chat.completions.create(model=LLM_ENDPOINT, messages=messages, max_tokens=LLM_MAX_TOKENS, temperature=LLM_TEMPERATURE)
    messages.append({"role": "assistant", "content": final.choices[0].message.content})
    return {"response": final.choices[0].message.content, "tool_calls_made": tool_calls_made, "messages": messages}

print("✅ contractor_agent() ready")

# COMMAND ----------

# DBTITLE 1,Demo Scenarios
# MAGIC %md
# MAGIC ## Demo Scenarios
# MAGIC 1. **Wave staffing** — Find contractors for a specific wave×state
# MAGIC 2. **Contractor vetting** — Deep-dive on a candidate's incident history
# MAGIC 3. **Capacity gap analysis** — Check existing assignments and find reinforcements

# COMMAND ----------

# DBTITLE 1,Scene 1 — Wave staffing: Find contractors for 2027-Q1 in CO
result_1 = contractor_agent(
    "We need contractors for the 2027-Q1 copper retirement wave in Colorado. "
    "What are the best available options? We need underground boring and general construction."
)
print("\n" + "=" * 80)
print("SCENE 1: WAVE STAFFING — 2027-Q1, Colorado")
print("=" * 80)
print(result_1["response"][:2500])
print(f"\n🛠️ Tool calls: {len(result_1['tool_calls_made'])}")

# COMMAND ----------

# DBTITLE 1,Scene 2 — Contractor vetting deep-dive
# Pick the top contractor from Scene 1 for a deep dive
result_2 = contractor_agent(
    "I want to vet Prairie Fiber Co before we assign them. "
    "What's their incident history and fault rate? Any safety concerns?"
)
print("\n" + "=" * 80)
print("SCENE 2: CONTRACTOR VETTING")
print("=" * 80)
print(result_2["response"][:2500])
print(f"\n🛠️ Tool calls: {len(result_2['tool_calls_made'])}")

# COMMAND ----------

# DBTITLE 1,Scene 3 — Capacity gap analysis
result_3 = contractor_agent(
    "Show me all current contractor assignments for Arizona. "
    "Are we fully staffed for 2026-Q4? If not, who should we add?"
)
print("\n" + "=" * 80)
print("SCENE 3: CAPACITY GAP ANALYSIS — Arizona")
print("=" * 80)
print(result_3["response"][:2500])
print(f"\n🛠️ Tool calls: {len(result_3['tool_calls_made'])}")