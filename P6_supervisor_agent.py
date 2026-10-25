# Databricks notebook source
# DBTITLE 1,Copper Retirement — Agents Build & Eval (Consolidated)
# MAGIC %md
# MAGIC # Copper Retirement — Agents Build & Eval (Consolidated)
# MAGIC # project: copper-retirement | developer: copper-ml
# MAGIC
# MAGIC **Consolidated notebook** combining Supervisor, Dig-Triage, Contractor Sourcing agents + evaluation harness.
# MAGIC
# MAGIC ## Part 1: Supervisor Agent
# MAGIC Meta-agent that routes user queries to specialized sub-agents and synthesizes responses.
# MAGIC
# MAGIC **Sub-agents (tools):**
# MAGIC 1. **regulatory_query** — RAG over FCC/PUC regulatory documents (Vector Search + FMAPI)
# MAGIC 2. **triage_incident** — Dig-safe incident triage with geospatial tools (UC SQL functions)
# MAGIC 3. **find_contractors** — Contractor search, vetting, and wave assignment lookup
# MAGIC 4. **commodity_forecast** — Copper commodity price trends and sell/hold signals
# MAGIC
# MAGIC ## Part 2: Standalone Sub-Agents
# MAGIC Dig-triage and contractor-sourcing agents with independent tool-calling loops for unit testing.
# MAGIC
# MAGIC ## Part 3: Agent Evaluation Sets
# MAGIC 75 labeled test cases (25 per agent) with MLflow tracing + scoring harness + serving promotion gate.
# MAGIC
# MAGIC ## Part 4: Regulatory RAG Eval (real sources)
# MAGIC 38-question eval set (`reg_rag_eval_dataset` v3: FCC, 811/one-call, OSHA, EPA, state PUC, ROW; 30 answerable + 8 flag-gap) with citation scorers: citation present, citation URL valid (must be an official URL in `regulatory_source_register`), expected citation, jurisdiction correctness, fact regex, LLM-judge groundedness, and gap abstention. **Answers without citations fail.** Results append to `reg_rag_eval_results`.
# MAGIC
# MAGIC The regulatory RAG chain (cell *Regulatory RAG chain*) retrieves **only `is_synthetic = false` chunks**. It queries the VS index first and falls back to Delta TF-IDF over real chunks until ACC-REG-VS-RESYNC re-syncs the index.
# MAGIC
# MAGIC **Architecture:** Supervisor LLM → tool-calling dispatch → sub-agent execution → response synthesis
# MAGIC **LLM:** `databricks-meta-llama-3-3-70b-instruct`
# MAGIC **Consolidation:** Merged from P6_supervisor_agent + P6_dig_triage_agent + P6_contractor_sourcing_agent + P6_agent_eval_sets_v2 (2026-10-24, ACC-NB-AGENTS-CONSOLIDATE) + P6_regulatory_rag_chain (2026-10-24, ACC-REG-RAG-EVAL)

# COMMAND ----------

# DBTITLE 1,Configuration + clients
from databricks.sdk import WorkspaceClient
from openai import OpenAI
import json

LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.1
# Parameterized (ACC-DE-PARAMETERIZE): defaults match bundle variables catalog_name/schema_name
dbutils.widgets.text("catalog", "cdm_tmforum")
dbutils.widgets.text("schema", "copper_retirement")
dbutils.widgets.text("experiment_path", "")  # blank = <this notebook's folder>/experiments/agent_eval_sets
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")

w = WorkspaceClient()
_api_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
llm_client = OpenAI(api_key=_api_token, base_url=f"{w.config.host}/serving-endpoints")
print(f"✅ Supervisor initialized: {LLM_ENDPOINT}")

# COMMAND ----------

# DBTITLE 1,Regulatory RAG chain (real sources, citation-required)
# Merged from P6_regulatory_rag_chain (ACC-REG-RAG-EVAL, 2026-10-24). Retrieval is restricted to REAL sources
# (regulatory_doc_chunks.is_synthetic = false). Every answer must cite official URLs from regulatory_source_register.
import re, json
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

VS_INDEX_NAME = f"{CATALOG}.{SCHEMA}.regulatory_doc_chunks_vs_index"   # lives on VS endpoint cmeg-demos-vs (DEC-VS-ENDPOINT-ACTUAL)
REG_TOP_K = 6
# Llama-3.3-70B AI Gateway input guardrail flags statute text as "non-violent-crimes" (false positive, 2026-10-24) -> use Claude for RAG
REG_LLM_ENDPOINT = "databricks-claude-sonnet-4-5"
JUDGE_ENDPOINT = "databricks-gpt-oss-120b"   # different model family than the generator
REG_COLUMNS = ["chunk_id", "source_id", "title", "citation", "jurisdiction", "source_url", "embedding_text"]

# Official-source allowlist = register (every citation must resolve to one of these URLs)
_REGISTER = {r.source_id: r.asDict() for r in spark.table(f"{CATALOG}.{SCHEMA}.regulatory_source_register").collect()}
OFFICIAL_URLS = {v["official_url"].rstrip("/"): v for v in _REGISTER.values() if v.get("official_url")}
# Also allow chunk-level official URLs (sub-section pages downloaded for a registered source), mapped to that register row
for _r in spark.sql(f"SELECT DISTINCT source_id, source_url FROM {CATALOG}.{SCHEMA}.regulatory_doc_chunks WHERE is_synthetic = false AND source_url IS NOT NULL").collect():
    if _r.source_id in _REGISTER: OFFICIAL_URLS.setdefault(_r.source_url.rstrip("/"), _REGISTER[_r.source_id])

# Delta fallback retriever over REAL chunks only (used until the VS index is re-synced with real docs)
_REAL = spark.sql(f"""SELECT {', '.join(REG_COLUMNS)} FROM {CATALOG}.{SCHEMA}.regulatory_doc_chunks
                     WHERE is_synthetic = false AND source_url IS NOT NULL""").toPandas()
_TFIDF = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True, min_df=1)
_TFIDF_M = _TFIDF.fit_transform(_REAL["embedding_text"].fillna(""))

def _retrieve_delta(query, top_k=REG_TOP_K, jurisdiction=None):
    sims = linear_kernel(_TFIDF.transform([query]), _TFIDF_M).ravel()
    df = _REAL.assign(score=sims)
    if jurisdiction:
        df = df[df["jurisdiction"].isin([jurisdiction, "US"])]
    df = df.sort_values("score", ascending=False)
    df = df.groupby("source_id", sort=False).head(2).head(top_k)   # source diversity
    return df.to_dict("records")

def _retrieve_tvf(query, top_k=REG_TOP_K, jurisdiction=None):
    """UC TVF search_regulatory_chunks: bge-large cosine over real chunks (ACC-REG-DL-ALT-1024). Used until the VS index is recreated."""
    df = spark.sql(f"SELECT * FROM {CATALOG}.{SCHEMA}.search_regulatory_chunks(:q, :k)", args={"q": query, "k": top_k * 5}).toPandas()
    df = df.rename(columns={"chunk_text": "embedding_text"})
    if jurisdiction:
        df = df[df["jurisdiction"].isin([jurisdiction, "US"])]
    df = df.sort_values("score", ascending=False).groupby("source_id", sort=False).head(2).head(top_k)
    return df.to_dict("records")

def _retrieve_vs(query, top_k=REG_TOP_K, jurisdiction=None):
    filt = {"is_synthetic": False}
    if jurisdiction: filt["jurisdiction"] = [jurisdiction, "US"]
    r = w.vector_search_indexes.query_index(index_name=VS_INDEX_NAME, columns=REG_COLUMNS,
                                            query_text=query, num_results=top_k, filters_json=json.dumps(filt))
    cols = [c.name for c in r.manifest.columns]
    return [dict(zip(cols, row)) for row in (r.result.data_array or [])]

def retrieve_regulatory_chunks(query, top_k=REG_TOP_K, jurisdiction=None):
    """VS first (real chunks only) -> UC TVF (bge-large over real chunks) -> Delta TF-IDF fallback."""
    try:
        hits = [h for h in _retrieve_vs(query, top_k, jurisdiction) if h.get("source_url")]
        if hits: return hits, "vector_search"
    except Exception:
        pass   # index not yet recreated with is_synthetic/source_url columns (ACC-VS-INDEX-RECREATE / ACC-REG-VS-RESYNC)
    try:
        hits = _retrieve_tvf(query, top_k, jurisdiction)
        if hits: return hits, "uc_tvf_bge"
    except Exception:
        pass
    return _retrieve_delta(query, top_k, jurisdiction), "delta_tfidf_fallback"

def format_context(chunks):
    if not chunks: return "NO SOURCES RETRIEVED."
    return "\n\n".join(
        f"[S{i}] {c['title']} | Citation: {c['citation']} | Jurisdiction: {c['jurisdiction']} | URL: {c['source_url']}\n{c['embedding_text'][:2500]}"
        for i, c in enumerate(chunks, 1))

REG_SYSTEM_PROMPT = """You are a regulatory compliance assistant for a telecom carrier retiring copper plant.
Answer ONLY from the numbered SOURCES. Rules:
1. Every factual sentence must end with a citation in the form [S#](URL) using the exact URL shown for that source.
2. Never cite a URL, rule number, deadline or docket that is not in the SOURCES. Never answer from memory.
3. Keep federal (US) and state rules distinct; name the jurisdiction for each requirement.
4. If the SOURCES do not contain the specific detail asked for, reply starting with "INSUFFICIENT SOURCES:" and say what is missing. Do not guess.
Be concise (<= 150 words)."""

def regulatory_rag_query(question, jurisdiction=None, top_k=REG_TOP_K):
    chunks, mode = retrieve_regulatory_chunks(question, top_k, jurisdiction)
    ctx = format_context(chunks)
    resp = llm_client.chat.completions.create(model=REG_LLM_ENDPOINT, temperature=0.0, max_tokens=600,
        messages=[{"role": "system", "content": REG_SYSTEM_PROMPT},
                  {"role": "user", "content": f"SOURCES:\n{ctx}\n\nQUESTION: {question}"}])
    return {"question": question, "answer": resp.choices[0].message.content, "retrieval_mode": mode,
            "sources": [{k: c.get(k) for k in ("source_id", "citation", "jurisdiction", "source_url")} for c in chunks],
            "context": ctx}

print(f"✅ Regulatory RAG ready: {len(_REAL):,} real chunks, {len(OFFICIAL_URLS)} official URLs, generator={REG_LLM_ENDPOINT}")

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
    """Regulatory sub-agent: grounded RAG over REAL sources only (see cell 'Regulatory RAG chain').
    Returns the cited answer plus official source URLs; never answers from memory."""
    try:
        out = regulatory_rag_query(question, jurisdiction=_ns(state_filter) if state_filter else None)
        return json.dumps({"agent": "regulatory", "answer": out["answer"], "retrieval_mode": out["retrieval_mode"],
                           "sources": out["sources"],
                           "instruction": "Repeat the [S#](URL) citations verbatim. Do not add rules or deadlines not in this answer."}, default=str)
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

# COMMAND ----------

# DBTITLE 1,Part 2: Standalone Sub-Agents
# MAGIC %md
# MAGIC ---
# MAGIC ## Part 2: Standalone Sub-Agents
# MAGIC
# MAGIC The following cells define the dig-triage and contractor-sourcing agents as **standalone tool-calling agents** (independent of the supervisor). Use these for unit testing, eval runs, and debugging individual agent behavior.
# MAGIC
# MAGIC *Consolidated from P6_dig_triage_agent and P6_contractor_sourcing_agent (2026-10-24).*

# COMMAND ----------

# DBTITLE 1,Dig-Triage Agent — Tool Definitions + Executor
# ══════════════════════════════════════════════════════════════
# DIG-TRIAGE AGENT — Standalone tool-calling agent
# Consolidated from P6_dig_triage_agent (ACC-NB-AGENTS-CONSOLIDATE)
# ══════════════════════════════════════════════════════════════

# Tool names mapping to UC functions
TRIAGE_TOOL_FUNCTIONS = {
    "incident_lookup": f"{CATALOG}.{SCHEMA}.incident_lookup",
    "proximity_search": f"{CATALOG}.{SCHEMA}.proximity_search",
    "reroute_suggest": f"{CATALOG}.{SCHEMA}.reroute_suggest",
}

MAX_PROXIMITY_ROWS = 20

TRIAGE_TOOLS = [
    {"type": "function", "function": {
        "name": "incident_lookup",
        "description": "Look up full details for a specific dig-safe incident by ID. Returns severity, location, cable damage type, root cause, triage priority, nearest copper device, impacted services/customers, wire center, and recommended action.",
        "parameters": {"type": "object", "properties": {
            "incident_id": {"type": "integer", "description": "The unique incident ID (e.g. 200001). IDs range from 200001 to 205000."}
        }, "required": ["incident_id"]}
    }},
    {"type": "function", "function": {
        "name": "proximity_search",
        "description": "Search for dig-safe incidents near a geographic location. Returns all incidents within the specified radius, sorted by distance.",
        "parameters": {"type": "object", "properties": {
            "latitude": {"type": "number", "description": "Latitude of search center (decimal degrees)"},
            "longitude": {"type": "number", "description": "Longitude of search center (decimal degrees)"},
            "radius_km": {"type": "number", "description": "Search radius in km (default 25)"}
        }, "required": ["latitude", "longitude"]}
    }},
    {"type": "function", "function": {
        "name": "reroute_suggest",
        "description": "Get rerouting and remediation recommendations for a specific dig-safe incident. Recommends: FIBER_MIGRATION, COPPER_REROUTE, EMERGENCY_RESTORE, TEMPORARY_BYPASS, REPAIR_IN_PLACE, or MONITOR_ONLY.",
        "parameters": {"type": "object", "properties": {
            "incident_id": {"type": "integer", "description": "The incident ID to generate reroute recommendations for."}
        }, "required": ["incident_id"]}
    }}
]


def _triage_serialize_rows(rows):
    for row in rows:
        for k, v in row.items():
            if hasattr(v, 'isoformat'): row[k] = v.isoformat()
            elif isinstance(v, (bytes, bytearray)): row[k] = str(v)
            elif v is not None and not isinstance(v, (str, int, float, bool, list, dict)): row[k] = str(v)
    return rows


def triage_execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a UC SQL function for the triage agent."""
    if tool_name == "incident_lookup":
        query = f"SELECT * FROM {TRIAGE_TOOL_FUNCTIONS['incident_lookup']}({arguments['incident_id']})"
    elif tool_name == "proximity_search":
        lat, lon = arguments['latitude'], arguments['longitude']
        radius = arguments.get('radius_km', 25.0)
        query = f"SELECT * FROM {TRIAGE_TOOL_FUNCTIONS['proximity_search']}({lat}, {lon}, {radius})"
    elif tool_name == "reroute_suggest":
        query = f"SELECT * FROM {TRIAGE_TOOL_FUNCTIONS['reroute_suggest']}({arguments['incident_id']})"
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        df = spark.sql(query)
        rows = _triage_serialize_rows([row.asDict() for row in df.collect()])
        if tool_name == "proximity_search" and len(rows) > MAX_PROXIMITY_ROWS:
            priorities, severities = {}, {}
            for r in rows:
                p = r.get('triage_priority', 'unknown'); priorities[p] = priorities.get(p, 0) + 1
                s = r.get('severity', 'unknown'); severities[s] = severities.get(s, 0) + 1
            result = {"tool": tool_name, "total_incidents_in_radius": len(rows),
                      "summary": {"by_priority": priorities, "by_severity": severities},
                      "closest_incidents": rows[:MAX_PROXIMITY_ROWS]}
        else:
            result = {"tool": tool_name, "row_count": len(rows), "data": rows}
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"tool": tool_name, "error": str(e)})

print("✅ Triage tools defined")

# COMMAND ----------

# DBTITLE 1,Dig-Triage Agent — System Prompt + Agent Loop
TRIAGE_SYSTEM_PROMPT = """You are a dig-safe incident triage agent for LakeLink Fiber, a telecommunications carrier actively retiring legacy copper infrastructure and migrating customers to fiber.

Your role is to help field operations teams quickly assess, prioritize, and respond to dig-safe incidents that damage copper cable plant. You have access to three tools:

1. **incident_lookup** — Get full details on a specific incident by ID.
2. **proximity_search** — Find all incidents near a geographic point within a radius.
3. **reroute_suggest** — Get recommended remediation action for an incident.

When triaging:
1. **Assess** — Look up the incident for severity, location, and impact scope.
2. **Contextualize** — Check for nearby incidents to identify patterns or clusters.
3. **Recommend** — Use reroute_suggest for the optimal remediation path.
4. **Summarize** — Clear triage summary with priority, impacted customers, recommended action, and rationale.

Guidelines:
- Always state the triage priority (P1=critical, P2=high, P3=medium, P4=low).
- Highlight fiber-ready wire centers as copper retirement acceleration opportunities.
- Flag repeat incidents in the same area.
- Use precise numbers for customer/service impact.
- End every response with a clear RECOMMENDED ACTION block.
"""


def triage_agent(
    user_message: str,
    conversation_history: list[dict] | None = None,
    max_tool_rounds: int = 5,
    verbose: bool = True,
) -> dict:
    """Run the standalone dig-triage agent with tool-calling loop."""
    messages = conversation_history.copy() if conversation_history else []
    if not messages or messages[0].get('role') != 'system':
        messages.insert(0, {'role': 'system', 'content': TRIAGE_SYSTEM_PROMPT})
    messages.append({'role': 'user', 'content': user_message})
    tool_calls_made = []
    for round_num in range(max_tool_rounds):
        response = llm_client.chat.completions.create(
            model=LLM_ENDPOINT, messages=messages, tools=TRIAGE_TOOLS,
            tool_choice='auto', max_tokens=LLM_MAX_TOKENS, temperature=LLM_TEMPERATURE
        )
        assistant_msg = response.choices[0].message
        msg_dict = {'role': 'assistant', 'content': assistant_msg.content or ''}
        if assistant_msg.tool_calls:
            msg_dict['tool_calls'] = [{'id': tc.id, 'type': 'function', 'function': {'name': tc.function.name, 'arguments': tc.function.arguments}} for tc in assistant_msg.tool_calls]
        messages.append(msg_dict)
        if not assistant_msg.tool_calls:
            if verbose: print(f'\n✅ Triage agent responded after {round_num} tool-calling round(s)')
            return {'response': assistant_msg.content, 'tool_calls_made': tool_calls_made, 'messages': messages}
        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            if verbose: print(f'  🛠️  Round {round_num + 1}: {fn_name}({json.dumps(fn_args)})')
            result_str = triage_execute_tool(fn_name, fn_args)
            tool_calls_made.append({'tool': fn_name, 'arguments': fn_args, 'result_preview': result_str[:500]})
            messages.append({'role': 'tool', 'tool_call_id': tc.id, 'content': result_str})
    # Fallback
    messages.append({'role': 'user', 'content': 'Please provide your triage summary now.'})
    final = llm_client.chat.completions.create(model=LLM_ENDPOINT, messages=messages, max_tokens=LLM_MAX_TOKENS, temperature=LLM_TEMPERATURE)
    return {'response': final.choices[0].message.content, 'tool_calls_made': tool_calls_made, 'messages': messages}

print('✅ triage_agent() ready')

# COMMAND ----------

# DBTITLE 1,Contractor Sourcing Agent — Tool Definitions + Executor
# ══════════════════════════════════════════════════════════════
# CONTRACTOR SOURCING AGENT — Standalone tool-calling agent
# Consolidated from P6_contractor_sourcing_agent (ACC-NB-AGENTS-CONSOLIDATE)
# ══════════════════════════════════════════════════════════════

MAX_SEARCH_ROWS = 15

CONTRACTOR_TOOLS = [
    {"type": "function", "function": {
        "name": "search_contractors",
        "description": "Search the contractor registry for contractors matching given criteria. Returns ranked list by composite score (safety 40%% + rating 30%% + SLA 30%%). Can filter by state, contractor type, minimum safety score, and certification.",
        "parameters": {"type": "object", "properties": {
            "state": {"type": "string", "description": "US state code (e.g. 'CO', 'OR', 'AZ')"},
            "contractor_type": {"type": "string", "description": "Specialty type: underground_boring, aerial_line, general_construction, fiber_splicing, cable_removal"},
            "min_safety_score": {"type": "number", "description": "Minimum safety score (0-100, default 70)"},
            "certified_only": {"type": "boolean", "description": "If true, only return OSHA/ISNetworld certified"}
        }, "required": []}
    }},
    {"type": "function", "function": {
        "name": "contractor_incidents",
        "description": "Get dig-safe incident history and fault rate for a named contractor.",
        "parameters": {"type": "object", "properties": {
            "contractor_name": {"type": "string", "description": "Full contractor name to look up"}
        }, "required": ["contractor_name"]}
    }},
    {"type": "function", "function": {
        "name": "wave_assignments",
        "description": "Check current contractor assignments for a retirement wave/state.",
        "parameters": {"type": "object", "properties": {
            "wave": {"type": "string", "description": "Retirement wave (e.g. '2026-Q4', '2027-Q1')"},
            "state": {"type": "string", "description": "US state code (e.g. 'AZ')"}
        }, "required": []}
    }}
]


def contractor_execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute SQL queries against contractor UC tables."""
    try:
        if tool_name == 'search_contractors':
            conditions = []
            if arguments.get('state'): conditions.append(f"primary_state = '{arguments['state']}'")
            if arguments.get('contractor_type'): conditions.append(f"contractor_type = '{arguments['contractor_type']}'")
            if arguments.get('min_safety_score'): conditions.append(f"safety_score >= {arguments['min_safety_score']}")
            if arguments.get('certified_only'): conditions.append("osha_certified = true")
            where = ' AND '.join(conditions) if conditions else '1=1'
            query = f"""SELECT contractor_name, contractor_type, primary_state, safety_score, overall_rating, sla_compliance,
                       osha_certified, (safety_score*0.4 + overall_rating*20*0.3 + sla_compliance*0.3) as composite_score
                FROM {CATALOG}.{SCHEMA}.gold_contractor_scorecard WHERE {where}
                ORDER BY composite_score DESC LIMIT {MAX_SEARCH_ROWS}"""
        elif tool_name == 'contractor_incidents':
            name = arguments['contractor_name'].replace("'", "''")
            query = f"""SELECT contractor_name, incident_id, incident_date, severity, fault_type, state,
                       cable_damage_type, root_cause, resolution_hours
                FROM {CATALOG}.{SCHEMA}.contractor_incident_history
                WHERE contractor_name ILIKE '%{name}%' ORDER BY incident_date DESC LIMIT 20"""
        elif tool_name == 'wave_assignments':
            conditions = []
            if arguments.get('wave'): conditions.append(f"retirement_wave = '{arguments['wave']}'")
            if arguments.get('state'): conditions.append(f"state = '{arguments['state']}'")
            where = ' AND '.join(conditions) if conditions else '1=1'
            query = f"SELECT * FROM {CATALOG}.{SCHEMA}.gold_contractor_assignment_plan WHERE {where}"
        else:
            return json.dumps({'error': f'Unknown tool: {tool_name}'})
        df = spark.sql(query)
        rows = _ser([row.asDict() for row in df.collect()])
        return json.dumps({'tool': tool_name, 'row_count': len(rows), 'data': rows}, default=str)
    except Exception as e:
        return json.dumps({'tool': tool_name, 'error': str(e)})

print('✅ Contractor tools defined')

# COMMAND ----------

# DBTITLE 1,Contractor Sourcing Agent — System Prompt + Agent Loop
CONTRACTOR_SYSTEM_PROMPT = """You are a contractor sourcing agent for LakeLink Fiber's copper retirement program.

Your role is to help project managers find, evaluate, and recommend contractors for copper retirement field work — cable removal, fiber installation, aerial line work, and underground boring. You have three tools:

1. **search_contractors** — Search the contractor registry by state, type, safety score, and certification. Returns ranked list by composite score.
2. **contractor_incidents** — Get dig-safe incident history and fault rate for a specific contractor. Use to vet candidates.
3. **wave_assignments** — See which contractors are already assigned to a retirement wave/state. Use to check existing capacity.

When sourcing contractors:
1. Start with search_contractors to find qualified candidates matching the criteria.
2. Vet top candidates with contractor_incidents to check safety history.
3. Check wave_assignments to understand existing capacity and gaps.
4. Recommend a ranked shortlist with rationale.

Always include safety scores, incident rates, and certifications in your recommendations.
"""


def contractor_agent(
    user_message: str,
    conversation_history: list[dict] | None = None,
    max_tool_rounds: int = 5,
    verbose: bool = True,
) -> dict:
    """Run the standalone contractor sourcing agent with tool-calling loop."""
    messages = conversation_history.copy() if conversation_history else []
    if not messages or messages[0].get('role') != 'system':
        messages.insert(0, {'role': 'system', 'content': CONTRACTOR_SYSTEM_PROMPT})
    messages.append({'role': 'user', 'content': user_message})
    tool_calls_made = []
    for round_num in range(max_tool_rounds):
        response = llm_client.chat.completions.create(
            model=LLM_ENDPOINT, messages=messages, tools=CONTRACTOR_TOOLS,
            tool_choice='auto', max_tokens=LLM_MAX_TOKENS, temperature=LLM_TEMPERATURE
        )
        assistant_msg = response.choices[0].message
        msg_dict = {'role': 'assistant', 'content': assistant_msg.content or ''}
        if assistant_msg.tool_calls:
            msg_dict['tool_calls'] = [{'id': tc.id, 'type': 'function', 'function': {'name': tc.function.name, 'arguments': tc.function.arguments}} for tc in assistant_msg.tool_calls]
        messages.append(msg_dict)
        if not assistant_msg.tool_calls:
            if verbose: print(f'\n✅ Contractor agent responded after {round_num} tool-calling round(s)')
            return {'response': assistant_msg.content, 'tool_calls_made': tool_calls_made, 'messages': messages}
        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            if verbose: print(f'  🛠️  Round {round_num + 1}: {fn_name}({json.dumps(fn_args)})')
            result_str = contractor_execute_tool(fn_name, fn_args)
            tool_calls_made.append({'tool': fn_name, 'arguments': fn_args, 'result_preview': result_str[:500]})
            messages.append({'role': 'tool', 'tool_call_id': tc.id, 'content': result_str})
    messages.append({'role': 'user', 'content': 'Please provide your contractor recommendation now.'})
    final = llm_client.chat.completions.create(model=LLM_ENDPOINT, messages=messages, max_tokens=LLM_MAX_TOKENS, temperature=LLM_TEMPERATURE)
    return {'response': final.choices[0].message.content, 'tool_calls_made': tool_calls_made, 'messages': messages}

print('✅ contractor_agent() ready')

# COMMAND ----------

# DBTITLE 1,Part 3: Agent Evaluation Sets (75 cases)
# MAGIC %md
# MAGIC ---
# MAGIC ## Part 3: Agent Evaluation Sets & Scoring Harness
# MAGIC
# MAGIC 75 labeled test cases (25 triage + 25 contractor + 25 supervisor) with MLflow tracing, keyword scoring, tool-routing accuracy, and a serving promotion gate.
# MAGIC
# MAGIC *Consolidated from P6_agent_eval_sets_v2 (2026-10-24, ACC-NB-AGENTS-CONSOLIDATE).*

# COMMAND ----------

# DBTITLE 1,Eval Sets — Load from Delta + MLflow Setup
# ══════════════════════════════════════════════════════════════
# EVALUATION SETS — Read from persisted Delta tables
# Original 75 cases written by P6_agent_eval_sets_v2, now consolidated here
# ══════════════════════════════════════════════════════════════

import mlflow
from mlflow.tracking import MlflowClient
from datetime import datetime
import json, re, time
from typing import Callable, Dict, List, Optional

PROJECT_TAGS = {"telco_project": "copper-retirement", "developer": "copper-ml"}
EVAL_VERSION = "v2"

# Create/get experiment
import os
_nb_dir = os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
EXPERIMENT_PATH = dbutils.widgets.get("experiment_path").strip() or f"{_nb_dir}/experiments/agent_eval_sets"
exp = mlflow.set_experiment(EXPERIMENT_PATH)
client = MlflowClient()
client.set_experiment_tag(exp.experiment_id, "telco_project", "copper-retirement")
client.set_experiment_tag(exp.experiment_id, "eval_version", EVAL_VERSION)

# Load eval sets from Delta (75 cases: 25 triage + 25 contractor + 25 supervisor)
eval_df = spark.sql(f"SELECT * FROM {CATALOG}.{SCHEMA}.agent_eval_dataset_v2")
print(f"Loaded {eval_df.count()} eval cases from Delta")

# Split by agent
triage_eval_rows = [row.asDict() for row in eval_df.filter("agent = 'triage'").collect()]
contractor_eval_rows = [row.asDict() for row in eval_df.filter("agent = 'contractor'").collect()]
supervisor_eval_rows = [row.asDict() for row in eval_df.filter("agent = 'supervisor'").collect()]

print(f"  Triage: {len(triage_eval_rows)} cases")
print(f"  Contractor: {len(contractor_eval_rows)} cases")
print(f"  Supervisor: {len(supervisor_eval_rows)} cases")

# Enable MLflow tracing
mlflow.openai.autolog(log_traces=True, log_models=False, log_input_examples=False)
print(f"\nMLflow Experiment: {exp.name}")
print("MLflow Tracing: enabled")

# COMMAND ----------

# DBTITLE 1,Scoring Harness — Agent Eval Runner
def score_response(response_text: str, expected_contains: List[str]) -> dict:
    """Score a response against expected_contains keywords."""
    response_lower = response_text.lower()
    matched = [kw for kw in expected_contains if kw.lower() in response_lower]
    missed = [kw for kw in expected_contains if kw.lower() not in response_lower]
    score = len(matched) / len(expected_contains) if expected_contains else 1.0
    return {"matched": matched, "missed": missed, "score": round(score, 3), "pass": score >= 0.5}

def score_tool_usage(trace_tools: List[str], expected_tool: str) -> dict:
    """Score whether the agent called the correct tool(s)."""
    expected = [t.strip() for t in expected_tool.split(",") if t.strip()]
    if not expected:
        return {"expected": [], "called": trace_tools, "correct": True, "score": 1.0}
    called_set = set(trace_tools)
    expected_set = set(expected)
    matched = expected_set.intersection(called_set)
    score = len(matched) / len(expected_set) if expected_set else 1.0
    return {"expected": expected, "called": trace_tools, "correct": expected_set.issubset(called_set), "score": round(score, 3)}

def score_routing(actual_route: str, expected_route: str) -> dict:
    """Score supervisor routing correctness."""
    expected = [r.strip() for r in expected_route.split(",") if r.strip()]
    actual = [r.strip() for r in actual_route.split(",") if r.strip()]
    if not expected:
        return {"expected": [], "actual": actual, "correct": True, "score": 1.0}
    expected_set, actual_set = set(expected), set(actual)
    matched = expected_set.intersection(actual_set)
    score = len(matched) / len(expected_set) if expected_set else 1.0
    return {"expected": expected, "actual": actual, "correct": expected_set == actual_set, "score": round(score, 3)}

def run_agent_eval(
    agent_fn: Callable[[str], dict],
    eval_cases: List[dict],
    agent_name: str,
    experiment_id: str,
) -> List[dict]:
    """Run evaluation harness for an agent.
    agent_fn(input) -> {response: str, tools_called: list, routes: str, latency_ms: int}"""
    results = []
    with mlflow.start_run(
        experiment_id=experiment_id,
        run_name=f"{agent_name}_eval_{EVAL_VERSION}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
        tags={**PROJECT_TAGS, "eval_agent": agent_name, "eval_version": EVAL_VERSION},
    ) as parent_run:
        total_pass, total_cases = 0, len(eval_cases)
        category_scores = {}
        for case in eval_cases:
            with mlflow.start_run(run_name=f"{case['eval_id']}_{case['category']}", nested=True,
                                  tags={**PROJECT_TAGS, "eval_id": case["eval_id"], "difficulty": case["difficulty"]}):
                try:
                    result = agent_fn(case["input"])
                except Exception as e:
                    result = {"response": f"ERROR: {e}", "tools_called": [], "routes": "", "latency_ms": 0}
                expected_kw = json.loads(case["expected_contains"]) if isinstance(case["expected_contains"], str) else case["expected_contains"]
                content_score = score_response(result["response"], expected_kw)
                tool_score = score_tool_usage(result.get("tools_called", []), case.get("expected_tool", ""))
                route_score = score_routing(result.get("routes", ""), case.get("expected_route", ""))
                if case.get("expected_route"):
                    composite = 0.5 * content_score["score"] + 0.5 * route_score["score"]
                elif case.get("expected_tool"):
                    composite = 0.5 * content_score["score"] + 0.5 * tool_score["score"]
                else:
                    composite = content_score["score"]
                passed = composite >= 0.5
                if passed: total_pass += 1
                cat = case["category"]
                category_scores.setdefault(cat, []).append(composite)
                mlflow.log_params({"eval_id": case["eval_id"], "category": cat, "difficulty": case["difficulty"], "input": case["input"][:250]})
                mlflow.log_metrics({"content_score": content_score["score"], "tool_score": tool_score["score"],
                                    "route_score": route_score["score"], "composite_score": composite,
                                    "passed": 1 if passed else 0, "latency_ms": result.get("latency_ms", 0)})
                results.append({"eval_id": case["eval_id"], "agent": agent_name, "category": cat,
                                "difficulty": case["difficulty"], "input": case["input"],
                                "response_preview": result["response"][:200],
                                "content_score": content_score["score"], "tool_score": tool_score["score"],
                                "route_score": route_score["score"], "composite_score": composite,
                                "passed": passed, "missed_keywords": content_score["missed"],
                                "latency_ms": result.get("latency_ms", 0)})
        pass_rate = total_pass / total_cases if total_cases else 0
        mlflow.log_metrics({"overall_pass_rate": round(pass_rate, 3), "total_cases": total_cases,
                            "total_passed": total_pass, "total_failed": total_cases - total_pass})
        for cat, scores in category_scores.items():
            mlflow.log_metric(f"category_{cat}_avg", round(sum(scores)/len(scores), 3))
        print(f"\n{'='*60}")
        print(f"{agent_name.upper()} EVALUATION: {total_pass}/{total_cases} ({pass_rate:.1%})")
        for cat, scores in sorted(category_scores.items()):
            print(f"  {cat}: {sum(scores)/len(scores):.1%} ({len(scores)} cases)")
    return results

print("\u2705 Scoring harness ready: score_response, score_tool_usage, score_routing, run_agent_eval")

# COMMAND ----------

# DBTITLE 1,Serving Promotion Gate
def evaluate_gate(results: List[dict], agent_name: str) -> dict:
    """Apply serving promotion criteria.
    Gate: overall >= 80%, no category < 60%, hard >= 60%, no edge crashes."""
    agent_results = [r for r in results if r["agent"] == agent_name]
    if not agent_results:
        return {"agent": agent_name, "pass_gate": False, "blockers": ["No results found"]}
    total = len(agent_results)
    passed = sum(1 for r in agent_results if r["passed"])
    overall_rate = passed / total
    cat_scores = {}
    for r in agent_results:
        cat_scores.setdefault(r["category"], []).append(r["composite_score"])
    cat_rates = {cat: sum(s)/len(s) for cat, s in cat_scores.items()}
    hard_results = [r for r in agent_results if r["difficulty"] == "hard"]
    hard_rate = sum(1 for r in hard_results if r["passed"]) / len(hard_results) if hard_results else 1.0
    edge_results = [r for r in agent_results if "edge" in r["category"]]
    edge_crashes = [r for r in edge_results if "ERROR" in r.get("response_preview", "")]
    blockers = []
    if overall_rate < 0.80: blockers.append(f"Overall pass rate {overall_rate:.1%} < 80%")
    for cat, rate in cat_rates.items():
        if rate < 0.60: blockers.append(f"Category '{cat}' avg {rate:.1%} < 60%")
    if hard_rate < 0.60: blockers.append(f"Hard difficulty {hard_rate:.1%} < 60%")
    if edge_crashes: blockers.append(f"{len(edge_crashes)} edge case(s) crashed")
    return {"agent": agent_name, "pass_gate": len(blockers) == 0, "overall_rate": round(overall_rate, 3),
            "hard_rate": round(hard_rate, 3), "category_rates": {k: round(v, 3) for k, v in cat_rates.items()},
            "blockers": blockers, "total_cases": total, "total_passed": passed}

def print_gate_report(gate_results: List[dict]):
    """Print formatted gate report for all agents."""
    print(f"\n{'='*70}\nSERVING PROMOTION GATE REPORT\n{'='*70}")
    all_pass = True
    for g in gate_results:
        status = "\u2705 PASS" if g["pass_gate"] else "\u274c FAIL"
        print(f"\n{g['agent'].upper()}: {status}")
        print(f"  Overall: {g['overall_rate']:.1%} ({g['total_passed']}/{g['total_cases']})")
        print(f"  Hard: {g.get('hard_rate', 0):.1%}")
        if g.get('category_rates'):
            for cat, rate in sorted(g['category_rates'].items()):
                flag = ' \u26a0\ufe0f' if rate < 0.60 else ''
                print(f"    {cat}: {rate:.1%}{flag}")
        if g['blockers']:
            for b in g['blockers']: print(f"    \u2022 {b}")
            all_pass = False
    print(f"\n{'='*70}")
    if all_pass: print("VERDICT: All agents PASS. Ready for serving endpoint promotion.")
    else: print(f"VERDICT: {', '.join(g['agent'] for g in gate_results if not g['pass_gate'])} BLOCKED.")

print("\u2705 Gate evaluator ready.")
print("Usage: evaluate_gate(results, 'triage'), print_gate_report([...])")

# COMMAND ----------

# DBTITLE 1,Part 4: Regulatory RAG Eval (real sources)
# MAGIC %md
# MAGIC ## Part 4: Regulatory RAG Eval (real sources)
# MAGIC Merged from `P6_regulatory_rag_chain` (ACC-REG-RAG-EVAL). Eval set: `reg_rag_eval_dataset` v3 (38 questions: FCC 12, 811/one-call 12, state PUC 6, OSHA 3, ROW 3, EPA 1, multi-jurisdiction 1; 37 answerable + 1 flag-gap since 2026-10-25; 7 former parse/corpus gaps were flipped to answerable after ACC-REG-DL-ALT-1024 re-chunked them).
# MAGIC
# MAGIC * Expected citations come from `regulatory_source_register.official_url`. Expected facts are regexes checked against the real chunk text.
# MAGIC * **Flag-gap question** (REG-V3-37, AZ ACC R14-2-1107) covers a source that is registered but not indexed. The chain must answer `INSUFFICIENT SOURCES` and must not answer from memory.
# MAGIC * **Retrieval chain:** VS index -> UC TVF `search_regulatory_chunks` (bge-large, 1,598 real chunks) -> Delta TF-IDF. Citation allowlist = register `official_url` + chunk-level official `source_url` of registered sources.
# MAGIC * **Runs 2026-10-25 (ACC-ML-REG-EVAL-DELTA-SEARCH):** TVF on old labels 26/38 -> TVF on new labels 30/38. TF-IDF on new labels 31/38, hybrid RRF 30/38 (one uncited answer). Citation URL validity, jurisdiction correctness and gap abstention were 100% for TVF and TF-IDF. The remaining failures come from the generator (over-abstaining, plus one unsupported 47 CFR 51.333 cite), not from retrieval.
# MAGIC * **Gate:** overall pass >= 80%, citation URL validity = 100%, jurisdiction correctness = 100%, flag-gap abstention = 100%. An answer with no citation fails.

# COMMAND ----------

# DBTITLE 1,Regulatory RAG — scorers
# ---------- Scorers: answers without valid citations FAIL ----------
import re, json, concurrent.futures as cf
_URL_RE = re.compile(r"https?://[^\s\)\]>\"']+")
_ABSTAIN_RE = re.compile(r"INSUFFICIENT SOURCES|do(es)? not (contain|include|provide|specify)|not (found|available) in the (provided )?sources", re.I)

def _urls(text): return {u.rstrip(".,;:").rstrip("/") for u in _URL_RE.findall(text or "")}

def score_citation_present(ans, row):            # every answerable response must cite >=1 URL
    return len(_urls(ans)) > 0

def score_citation_url_valid(ans, row):          # every cited URL must be an official URL in the register
    u = _urls(ans); return bool(u) and all(x in OFFICIAL_URLS for x in u)

def score_expected_citation(ans, row):           # cites at least one expected official source
    return bool(_urls(ans) & {x.rstrip("/") for x in row["expected_citation_urls"]})

def score_jurisdiction(ans, row):                # cited sources are federal or the asked state; federal Qs cite only federal
    j = {OFFICIAL_URLS[x]["jurisdiction"] for x in _urls(ans) if x in OFFICIAL_URLS}
    if not j: return False
    allowed = {"US"} if row["jurisdiction"] == "US" else {"US", row["jurisdiction"]}
    ok = j <= allowed
    if row["jurisdiction"] != "US": ok = ok and row["jurisdiction"] in j
    return ok

def score_facts(ans, row):
    return all(re.search(f, ans or "", re.I) for f in row["expected_facts_regex"])

def score_abstain(ans, row):                     # flag-gap questions must abstain, not answer from memory
    return bool(_ABSTAIN_RE.search(ans or ""))

JUDGE_PROMPT = """You are grading a regulatory RAG answer for groundedness.
Return JSON {"grounded": true|false, "reason": "<short>"}. grounded=true only if EVERY factual claim (numbers, deadlines, rule cites) in ANSWER is directly supported by SOURCES. An answer that says the sources are insufficient is grounded if it makes no unsupported claims."""

def score_groundedness(ans, ctx):
    r = llm_client.chat.completions.create(model=JUDGE_ENDPOINT, temperature=0, max_tokens=2500,
        messages=[{"role": "system", "content": JUDGE_PROMPT},
                  {"role": "user", "content": f"SOURCES:\n{ctx[:14000]}\n\nANSWER:\n{ans}"}])
    c = r.choices[0].message.content
    if isinstance(c, list): c = " ".join(p.get("text", "") for p in c if isinstance(p, dict))
    m = re.search(r"\{.*\}", c or "", re.S)
    try: d = json.loads(m.group(0)); return bool(d.get("grounded")), d.get("reason", "")
    except Exception: return False, "judge_parse_error"

def evaluate_row(row):
    jur = None if row["jurisdiction"] == "US" else row["jurisdiction"]
    out = regulatory_rag_query(row["question"], jurisdiction=jur)
    a = out["answer"]; g, why = score_groundedness(a, out["context"])
    s = dict(eval_id=row["eval_id"], category=row["category"], jurisdiction=row["jurisdiction"], answerable=bool(row["answerable"]),
             answer=a, retrieval_mode=out["retrieval_mode"], retrieved_source_ids=[x["source_id"] for x in out["sources"]],
             cited_urls=sorted(_urls(a)), groundedness=g, groundedness_reason=why,
             retrieval_hit=bool(set(row["expected_source_ids"]) & {x["source_id"] for x in out["sources"]}))
    if row["answerable"]:
        s.update(citation_present=score_citation_present(a,row), citation_url_valid=score_citation_url_valid(a,row),
                 expected_citation=score_expected_citation(a,row), jurisdiction_correct=score_jurisdiction(a,row),
                 facts_correct=score_facts(a,row), abstained=score_abstain(a,row))
        s["passed"] = all([s["citation_present"], s["citation_url_valid"], s["jurisdiction_correct"], s["groundedness"], s["facts_correct"]])
    else:
        ab = score_abstain(a,row); urls_ok = all(x in OFFICIAL_URLS for x in _urls(a))
        s.update(citation_present=len(_urls(a))>0, citation_url_valid=urls_ok, expected_citation=None,
                 jurisdiction_correct=None, facts_correct=None, abstained=ab)
        s["passed"] = ab and urls_ok and g
    return s

def run_reg_rag_eval(eval_df, workers=6):
    with cf.ThreadPoolExecutor(workers) as ex:
        return list(ex.map(evaluate_row, [r for _, r in eval_df.iterrows()]))

print("✅ Regulatory scorers ready")

# COMMAND ----------

# DBTITLE 1,Regulatory RAG — run eval, persist results, gate
import datetime, pandas as pd
REG_EVAL_TABLE = f"{CATALOG}.{SCHEMA}.reg_rag_eval_dataset"
REG_RESULTS_TABLE = f"{CATALOG}.{SCHEMA}.reg_rag_eval_results"

reg_eval_df = spark.table(REG_EVAL_TABLE).where("eval_version = 'v3_real_sources'").toPandas()
R = pd.DataFrame(run_reg_rag_eval(reg_eval_df))
run_ts = datetime.datetime.now(datetime.timezone.utc)
R["run_id"] = f"reg-rag-v3-{R.retrieval_mode.iloc[0]}-" + run_ts.strftime("%Y%m%dT%H%M"); R["run_ts"] = run_ts
R["generator"] = REG_LLM_ENDPOINT; R["judge"] = JUDGE_ENDPOINT
for c in ["expected_citation", "jurisdiction_correct", "facts_correct"]: R[c] = R[c].astype("boolean")
spark.createDataFrame(R).write.mode("append").option("mergeSchema", "true").saveAsTable(REG_RESULTS_TABLE)

ans, gap = R[R.answerable], R[~R.answerable]
gate = {
    "overall_pass": R.passed.mean(),
    "citation_url_valid": ans.citation_url_valid.mean(),
    "jurisdiction_correct": ans.jurisdiction_correct.astype(float).mean(),
    "flag_gap_abstention": gap.abstained.mean() if len(gap) else 1.0,
}
blockers = [k for k, v in gate.items() if v < (0.80 if k == "overall_pass" else 1.0)]
print(f"Run {R.run_id[0]}: {int(R.passed.sum())}/{len(R)} passed | retrieval={R.retrieval_mode.unique().tolist()}")
for k, v in gate.items(): print(f"  {k}: {v:.1%}")
print("  by category:", R.groupby("category").passed.agg(['sum','count']).to_dict('index'))
print("GATE:", "✅ PASS" if not blockers else f"❌ FAIL {blockers}")
display(R[~R.passed][["eval_id", "category", "jurisdiction", "retrieved_source_ids", "abstained", "groundedness_reason"]])

# COMMAND ----------

# DBTITLE 1,Regulatory RAG — demo questions
# Demo questions carried over from P6_regulatory_rag_chain (now answered from real, cited sources)
for q, j in [("What are the FCC notice requirements and timelines for retiring copper telephone lines?", None),
             ("What are Colorado's requirements for discontinuing basic local exchange service beyond federal FCC rules?", "CO"),
             ("What is the Section 214 discontinuance process and when is an application automatically granted?", None)]:
    r = regulatory_rag_query(q, jurisdiction=j)
    print(f"\nQ: {q}\n[{r['retrieval_mode']}] {[s['source_id'] for s in r['sources']]}\n{r['answer']}\n" + "-" * 80)