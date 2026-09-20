# Databricks notebook source
# DBTITLE 1,P6 Supervisor Agent — Copper Retirement Multi-Agent Orchestrator
# MAGIC %md
# MAGIC # P6 Supervisor Agent — Copper Retirement
# MAGIC # project: copper-retirement | developer: copper-ml
# MAGIC
# MAGIC Meta-agent that routes user queries to specialized sub-agents and synthesizes responses.
# MAGIC
# MAGIC **Sub-agents (tools):**
# MAGIC 1. **regulatory_query** — RAG over FCC/PUC regulatory documents (Vector Search + FMAPI)
# MAGIC 2. **triage_incident** — Dig-safe incident triage with geospatial tools (UC SQL functions)
# MAGIC 3. **find_contractors** — Contractor search, vetting, and wave assignment lookup
# MAGIC 4. **commodity_forecast** — Copper commodity price trends and sell/hold signals
# MAGIC
# MAGIC **Architecture:** Supervisor LLM → tool-calling dispatch → sub-agent execution → response synthesis
# MAGIC
# MAGIC **LLM:** `databricks-meta-llama-3-3-70b-instruct`

# COMMAND ----------

# DBTITLE 1,Configuration + clients
from databricks.sdk import WorkspaceClient
from openai import OpenAI
import json

LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.1
CATALOG = "cdm_tmforum"
SCHEMA = "copper_retirement"

w = WorkspaceClient()
_api_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
llm_client = OpenAI(api_key=_api_token, base_url=f"{w.config.host}/serving-endpoints")
print(f"✅ Supervisor initialized: {LLM_ENDPOINT}")

# COMMAND ----------

# DBTITLE 1,Sub-agent tool definitions
SUPERVISOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "regulatory_query",
            "description": (
                "Ask a regulatory compliance question about copper retirement. "
                "Covers FCC rules (47 U.S.C. § 214, 47 C.F.R. §§ 63.71), state PUC filings, "
                "notice periods, Section 214 discontinuance, and carrier obligations. "
                "Returns answer with citations from regulatory source documents. "
                "Use for: notice period requirements, regulatory compliance, state-specific rules, filing obligations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Regulatory compliance question"},
                    "state_filter": {"type": "string", "description": "Optional: 2-letter state code to filter jurisdiction"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "triage_incident",
            "description": (
                "Triage a dig-safe incident on copper cable plant. Can look up a specific incident by ID, "
                "search for incidents near a location, or get reroute/remediation recommendations. "
                "Returns severity, priority (P1-P4), impacted customers/services, nearest device, "
                "and recommended action (fiber migration, copper reroute, emergency restore, etc.). "
                "Use for: incident assessment, geographic cluster analysis, reroute planning."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "request": {"type": "string", "description": "What to do: describe the incident ID, location, or what you need"}
                },
                "required": ["request"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_contractors",
            "description": (
                "Search for, evaluate, and recommend contractors for copper retirement field work. "
                "Can search by state and specialization, check incident/safety history, "
                "and show existing wave assignments. Returns ranked shortlists by composite score. "
                "Use for: contractor sourcing, vetting, capacity planning, wave staffing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "request": {"type": "string", "description": "What contractor info you need: state, type, vetting, or wave assignments"}
                },
                "required": ["request"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "commodity_forecast",
            "description": (
                "Get copper commodity price data, forecasts, and sell/hold signals. "
                "Queries price history, 30/60/90-day forecasts, and the sell/hold recommendation model. "
                "Use for: scrap timing decisions, price trend analysis, financial planning."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "request": {"type": "string", "description": "What commodity data you need: current prices, forecasts, sell/hold signal"}
                },
                "required": ["request"]
            }
        }
    }
]

# COMMAND ----------

# DBTITLE 1,Sub-agent executors
# --- Sub-agent implementations ---
# Each wraps the corresponding agent's core logic as a single-turn call

def _ser(rows):
    for r in rows:
        for k, v in r.items():
            if hasattr(v, 'isoformat'): r[k] = v.isoformat()
            elif v is not None and not isinstance(v, (str, int, float, bool, list, dict)): r[k] = str(v)
    return rows

_SC = {"alabama":"AL","alaska":"AK","arizona":"AZ","arkansas":"AR","california":"CA","colorado":"CO","connecticut":"CT","delaware":"DE","florida":"FL","georgia":"GA","hawaii":"HI","idaho":"ID","illinois":"IL","indiana":"IN","iowa":"IA","kansas":"KS","kentucky":"KY","louisiana":"LA","maine":"ME","maryland":"MD","massachusetts":"MA","michigan":"MI","minnesota":"MN","mississippi":"MS","missouri":"MO","montana":"MT","nebraska":"NE","nevada":"NV","new hampshire":"NH","new jersey":"NJ","new mexico":"NM","new york":"NY","north carolina":"NC","north dakota":"ND","ohio":"OH","oklahoma":"OK","oregon":"OR","pennsylvania":"PA","rhode island":"RI","south carolina":"SC","south dakota":"SD","tennessee":"TN","texas":"TX","utah":"UT","vermont":"VT","virginia":"VA","washington":"WA","west virginia":"WV","wisconsin":"WI","wyoming":"WY"}
def _ns(s): return _SC.get(s.strip().lower(), s.strip().upper()[:2]) if s else s
def _nt(t): return t.strip().lower().replace(" ","_") if t else t


def _exec_regulatory(question, state_filter=None):
    """Lightweight regulatory query — direct SQL lookup on enriched docs."""
    try:
        # Query the regulatory doc chunks table directly as a simplified RAG
        state_cond = f"AND jurisdiction_state_code = '{_ns(state_filter)}'" if state_filter else ""
        q = f"""
            SELECT title, embedding_text, docket_number, jurisdiction_state_code,
                   regulatory_topic, notice_period_days, issuing_body, document_status
            FROM {CATALOG}.{SCHEMA}.regulatory_doc_chunks
            WHERE embedding_text ILIKE '%{question.split()[0]}%' {state_cond}
            LIMIT 5
        """
        rows = _ser([r.asDict() for r in spark.sql(q).collect()])
        if not rows:
            return json.dumps({"agent": "regulatory", "answer": f"No regulatory documents found matching query. Use the dedicated P6_regulatory_rag_chain notebook for Vector Search RAG queries.", "sources": []}, default=str)
        return json.dumps({"agent": "regulatory", "matching_docs": len(rows), "data": rows, "note": "Simplified SQL lookup. For full RAG with embeddings, use P6_regulatory_rag_chain."}, default=str)
    except Exception as e:
        return json.dumps({"agent": "regulatory", "error": str(e)})


def _exec_triage(request):
    """Delegate to triage agent's UC functions based on request parsing."""
    try:
        # Try to extract incident ID from request
        import re
        ids = re.findall(r'\b(2\d{5})\b', request)
        if ids:
            iid = int(ids[0])
            # Get incident details + reroute suggestion
            q1 = f"SELECT * FROM {CATALOG}.{SCHEMA}.incident_lookup({iid})"
            q2 = f"SELECT reroute_option, reroute_rationale FROM {CATALOG}.{SCHEMA}.reroute_suggest({iid})"
            inc = _ser([r.asDict() for r in spark.sql(q1).collect()])
            reroute = _ser([r.asDict() for r in spark.sql(q2).collect()])
            return json.dumps({"agent": "triage", "incident": inc, "reroute": reroute}, default=str)
        
        # Try to extract coordinates for proximity search
        coords = re.findall(r'(-?\d+\.\d+)', request)
        if len(coords) >= 2:
            lat, lon = float(coords[0]), float(coords[1])
            radius = float(coords[2]) if len(coords) >= 3 else 25.0
            q = f"SELECT incident_id, state, severity, triage_priority, distance_from_search_km, impacted_service_count FROM {CATALOG}.{SCHEMA}.proximity_search({lat}, {lon}, {radius}) LIMIT 20"
            rows = _ser([r.asDict() for r in spark.sql(q).collect()])
            return json.dumps({"agent": "triage", "proximity_results": len(rows), "data": rows}, default=str)
        
        # General triage stats
        q = f"SELECT triage_priority, COUNT(*) as cnt FROM {CATALOG}.{SCHEMA}.silver_dig_incident_enriched GROUP BY triage_priority ORDER BY triage_priority"
        rows = _ser([r.asDict() for r in spark.sql(q).collect()])
        return json.dumps({"agent": "triage", "note": "Provide an incident ID (200001-205000) or lat/lon coordinates for specific triage.", "overall_stats": rows}, default=str)
    except Exception as e:
        return json.dumps({"agent": "triage", "error": str(e)})


def _exec_contractors(request):
    """Delegate to contractor-sourcing logic."""
    try:
        import re
        # Check for wave assignment queries
        wave_match = re.search(r'(\d{4}-Q[1-4])', request)
        # Prioritize full state name match over 2-letter word extraction
        state = None
        for name, code in sorted(_SC.items(), key=lambda x: -len(x[0])):
            if name in request.lower():
                state = code
                break
        if not state:
            sw = re.findall(r'\b([A-Z]{2})\b', request)
            for s in sw:
                if s in _SC.values() and s not in ('IN', 'OR', 'ME', 'HI', 'OK'):
                    state = s
                    break
        
        if wave_match:
            conds = [f"wave = '{wave_match.group(1)}'"]
            if state: conds.append(f"state_code = '{state}'")
            q = f"SELECT * FROM {CATALOG}.{SCHEMA}.gold_contractor_assignment_plan WHERE {' AND '.join(conds)} ORDER BY composite_score DESC"
            rows = _ser([r.asDict() for r in spark.sql(q).collect()])
            return json.dumps({"agent": "contractor", "type": "wave_assignments", "row_count": len(rows), "data": rows}, default=str)
        
        # Search contractors by state
        if state:
            q = f"""SELECT contractor_name, contractor_type, primary_state, dispatch_status, crew_size,
                    CAST(safety_score AS DOUBLE) AS safety_score, CAST(overall_rating AS DOUBLE) AS overall_rating,
                    ROUND((CAST(safety_score AS DOUBLE)/100)*0.4+(CAST(overall_rating AS DOUBLE)/5)*0.3+(CAST(sla_compliance_pct AS DOUBLE)/100)*0.3,4) AS composite_score
                FROM {CATALOG}.{SCHEMA}.gold_contractor_scorecard
                WHERE primary_state = '{state}' AND certification_status = 'fully_certified' AND safety_score >= 80
                ORDER BY composite_score DESC LIMIT 10"""
            rows = _ser([r.asDict() for r in spark.sql(q).collect()])
            return json.dumps({"agent": "contractor", "type": "search", "state": state, "row_count": len(rows), "data": rows}, default=str)
        
        return json.dumps({"agent": "contractor", "note": "Specify a state or wave (e.g. 2027-Q1) for contractor search."}, default=str)
    except Exception as e:
        return json.dumps({"agent": "contractor", "error": str(e)})


def _exec_commodity(request):
    """Query copper commodity price data and forecasts."""
    try:
        # Current price + recent trend
        q_recent = f"""
            SELECT price_date, region,
                   CAST(copper_lme_price_usd_ton AS DOUBLE) AS copper_lme_usd_ton,
                   CAST(copper_comex_price_usd_lb AS DOUBLE) AS copper_comex_usd_lb
            FROM {CATALOG}.{SCHEMA}.copper_commodity_price
            ORDER BY price_date DESC LIMIT 10
        """
        recent = _ser([r.asDict() for r in spark.sql(q_recent).collect()])
        
        # Forecast if available
        try:
            q_fc = f"SELECT * FROM {CATALOG}.{SCHEMA}.gold_commodity_price_forecast ORDER BY forecast_date DESC LIMIT 5"
            forecast = _ser([r.asDict() for r in spark.sql(q_fc).collect()])
        except:
            forecast = []
        
        # Sell/hold signal if available
        try:
            q_sig = f"SELECT * FROM {CATALOG}.{SCHEMA}.copper_commodity_sell_hold_signal LIMIT 1"
            signal = _ser([r.asDict() for r in spark.sql(q_sig).collect()])
        except:
            signal = []
        
        return json.dumps({"agent": "commodity", "recent_prices": recent, "forecasts": forecast, "sell_hold_signal": signal}, default=str)
    except Exception as e:
        return json.dumps({"agent": "commodity", "error": str(e)})


def execute_supervisor_tool(tool_name: str, arguments: dict) -> str:
    """Route supervisor tool calls to sub-agents."""
    if tool_name == "regulatory_query":
        return _exec_regulatory(arguments["question"], arguments.get("state_filter"))
    elif tool_name == "triage_incident":
        return _exec_triage(arguments["request"])
    elif tool_name == "find_contractors":
        return _exec_contractors(arguments["request"])
    elif tool_name == "commodity_forecast":
        return _exec_commodity(arguments["request"])
    else:
        return json.dumps({"error": f"Unknown sub-agent: {tool_name}"})

print("✅ Sub-agent executors ready")

# COMMAND ----------

# DBTITLE 1,SYSTEM_PROMPT — Supervisor Agent
SUPERVISOR_PROMPT = """You are the supervisor agent for LakeLink Fiber's copper retirement program. You coordinate a team of specialized agents to answer complex, multi-domain questions about copper plant retirement.

Your sub-agents:
1. **regulatory_query** — Regulatory compliance (FCC, state PUC, notice periods, filing requirements)
2. **triage_incident** — Dig-safe incident triage (severity, impact, reroute options, geographic clusters)
3. **find_contractors** — Contractor sourcing (search, vetting, wave assignments, capacity)
4. **commodity_forecast** — Copper price trends, forecasts, sell/hold timing signals

When to use multiple agents:
- "What should we do about incident X and which contractors can handle it?" → triage_incident + find_contractors
- "What are the regulatory requirements for retiring copper in CO and what's the price forecast for salvage?" → regulatory_query + commodity_forecast
- "Give me a full briefing on the Colorado retirement wave" → all agents

Guidelines:
- Route queries to the right specialist(s). Call multiple agents when the question spans domains.
- Synthesize responses into a unified briefing. Don't just relay raw data — add context and recommendations.
- Highlight cross-domain insights (e.g., a fiber-ready wire center + favorable commodity prices = accelerate retirement).
- Be executive-level concise: lead with the decision, then supporting detail.
- Always identify next actions and responsible parties.
"""

# COMMAND ----------

# DBTITLE 1,supervisor_agent — Multi-agent orchestration loop
def supervisor_agent(
    user_message: str,
    conversation_history: list[dict] | None = None,
    max_tool_rounds: int = 5,
    verbose: bool = True,
) -> dict:
    """Run the supervisor agent with multi-agent dispatch."""
    messages = conversation_history.copy() if conversation_history else []
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": SUPERVISOR_PROMPT})
    messages.append({"role": "user", "content": user_message})
    agents_called = []

    for round_num in range(max_tool_rounds):
        response = llm_client.chat.completions.create(
            model=LLM_ENDPOINT, messages=messages, tools=SUPERVISOR_TOOLS,
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
                print(f"\n✅ Supervisor responded after {round_num} routing round(s), agents called: {agents_called}")
            return {"response": amsg.content, "agents_called": agents_called, "messages": messages}

        for tc in amsg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            if verbose:
                print(f"  📡 Routing to {fn_name}: {json.dumps(fn_args)[:200]}")
            result_str = execute_supervisor_tool(fn_name, fn_args)
            agents_called.append(fn_name)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})

    # Fallback
    messages.append({"role": "user", "content": "Synthesize what you've gathered into a final briefing."})
    final = llm_client.chat.completions.create(model=LLM_ENDPOINT, messages=messages, max_tokens=LLM_MAX_TOKENS, temperature=LLM_TEMPERATURE)
    messages.append({"role": "assistant", "content": final.choices[0].message.content})
    return {"response": final.choices[0].message.content, "agents_called": agents_called, "messages": messages}

print("✅ supervisor_agent() ready")

# COMMAND ----------

# DBTITLE 1,Demo Scenarios
# MAGIC %md
# MAGIC ## Demo Scenarios
# MAGIC 1. **Single-domain routing** — Question goes to one sub-agent
# MAGIC 2. **Cross-domain synthesis** — Question spans triage + contractor domains
# MAGIC 3. **Full briefing** — Multi-agent query requiring all domains

# COMMAND ----------

# DBTITLE 1,Scene 1 — Single-domain: regulatory question
r1 = supervisor_agent(
    "What are the FCC notice period requirements for discontinuing copper service in Oregon?"
)
print("\n" + "=" * 80)
print("SCENE 1: SINGLE-DOMAIN REGULATORY QUERY")
print("=" * 80)
print(r1["response"][:2000])
print(f"\n📡 Agents called: {r1['agents_called']}")

# COMMAND ----------

# DBTITLE 1,Scene 2 — Cross-domain: incident + contractor dispatch
r2 = supervisor_agent(
    "We have a critical dig strike at incident 200204 in Oregon. "
    "I need the triage assessment AND the best available contractors in Oregon to handle emergency restoration."
)
print("\n" + "=" * 80)
print("SCENE 2: CROSS-DOMAIN TRIAGE + CONTRACTOR")
print("=" * 80)
print(r2["response"][:2500])
print(f"\n📡 Agents called: {r2['agents_called']}")

# COMMAND ----------

# DBTITLE 1,Scene 3 — Full briefing: multi-agent
r3 = supervisor_agent(
    "Give me a comprehensive briefing for our Arizona 2026-Q4 copper retirement wave. "
    "I need: current contractor assignments, copper scrap price outlook, "
    "and any regulatory considerations for Arizona."
)
print("\n" + "=" * 80)
print("SCENE 3: FULL MULTI-AGENT BRIEFING")
print("=" * 80)
print(r3["response"][:3000])
print(f"\n📡 Agents called: {r3['agents_called']}")