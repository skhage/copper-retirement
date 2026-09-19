# Lakelink Fiber — Copper Retirement Demo Script

**Date:** September 18, 2026  
**Version:** 1.0 — FINAL (Numbers Frozen)  
**Beats Covered:** Beat 1 (Copper Map) + Beat 4 (Regulatory Assistant)  
**Duration:** 8–10 minutes total  
**Data:** All data is SYNTHETIC (generated for demo purposes)  

---

## Frozen Headline KPIs (Reference Card)

Keep these numbers handy. All sourced from metric views, frozen as of Sep 18, 2026.

| Metric | Value | Source |
| --- | --- | --- |
| Annual Revenue at Risk | $604M | copper_ebitda_impact_achieved |
| Copper Circuits | 14,777 | copper_ebitda_impact_achieved |
| Copper Devices | 2,672 across 103 wire centers | copper_retirement_project_status |
| Critical Risk Devices | 383 (14.3%) | copper_retirement_project_status |
| Fiber Ready | 122 devices (4.6%) | copper_retirement_project_status |
| Customers Impacted | 288 (64 critical) | copper_customers_impacted |
| Services at Risk | 304 | copper_customers_impacted |
| Projected EBITDA Improvement | $32.2M over 6 quarters (Base) | copper_ebitda_impact_forecast |
| Immediate-Action Revenue | $214M (35.5% of total) | copper_ebitda_impact_achieved |
| High-Value Circuits | 1,777 (12%) → $328M (54% of revenue) | copper_ebitda_impact_achieved |
| SLA Breach Rate | 9.4% | copper_retirement_project_status |
| Avg Alarms per Device | 10.1 | copper_retirement_project_status |

---

## Pre-Demo Checklist

- [ ] Open `copper-map` app in browser (https://copper-map-{workspace}.databricks.app)
- [ ] Open `regulatory-assistant` app in a second tab (https://regulatory-assistant-{workspace}.databricks.app)
- [ ] Verify both apps show "LIVE DATA · SYNTHETIC" badge (not "MOCK DATA")
- [ ] Verify copper-map KPI bar populates (Copper Devices, Critical Risk %, Revenue at Risk)
- [ ] Verify regulatory-assistant KPI bar shows Documents count (should be 528)
- [ ] Clear any previous Genie chat history in copper-map
- [ ] Set regulatory-assistant jurisdiction filter to "All States"
- [ ] Ensure stable internet — both apps query live SQL warehouse and Vector Search

---

## BEAT 1: "Where Is Our Copper / Risk of Touching It?" (5 min)

### App: copper-map (Copper Prioritization Map)

---

### Scene 1: The Big Picture (60 sec)

**OPEN** the copper-map app. The audience sees the Lakelink Fiber branded header, a KPI bar, and a US map with colored bubbles.

**SAY:**
> "Let's start with the question every network planning VP asks: where is our copper, and how bad is it? This is the Copper Prioritization Map — a live Databricks App pulling from our unified data platform."

**POINT TO** the KPI cards across the top:

| Card | Expected Value | Talking Point |
| --- | --- | --- |
| Copper Devices | 2,672 | "Nearly 2,700 copper devices across our footprint" |
| Critical Risk | 14.3% | "One in seven devices is critical risk — needs immediate action" |
| Revenue at Risk | $298K MRR / $3.6M annualized | "Real revenue exposure tied to these assets" |
| Fiber Ready | 4.6% | "Only 5% are fiber-ready today — big migration ahead" |
| States | 6 | "Six-state footprint: CO, MN, WA, OR, ID, AZ" |
| Services Affected | 2,626 | "Over 2,600 services depend on this copper" |

**SAY:**
> "The map shows every wire center scored by retirement readiness. Bubble size is device count, color is risk tier — red is critical, orange is high, gray is medium, green is low."

---

### Scene 2: Drill Down by State (60 sec)

**CLICK** the State dropdown in the left sidebar → select **"OR" (Oregon)**.

**SAY:**
> "Let's drill into Oregon — one of our highest-risk states due to moisture and storm exposure."

**POINT TO** the map, which now shows only Oregon wire centers. Hover over the largest bubble (Portland area, critical risk).

**SAY (reading hover tooltip):**
> "Portland — critical risk score of 82, with nearly 4,000 alarms. This wire center alone needs immediate retirement planning."

**CLICK** the Risk Tier dropdown → select **"Critical"** to filter down further.

**SAY:**
> "When I filter to critical-only, we see exactly which locations demand capital allocation first. This is how the planning team prioritizes — they're not guessing, they're using ML risk scores."

**RESET** filters (clear both dropdowns) before moving to next scene.

---

### Scene 3: Ask the Copper Analytics Agent (90 sec)

**SCROLL DOWN** to the "Copper Analytics Agent" section (green dot, Genie-powered badge).

**SAY:**
> "Now here's where it gets interesting. Embedded right in the app is a Genie-powered analytics agent. Non-technical users can ask questions in plain English and get answers from the live data platform."

**CLICK** the suggested question chip: **"Which states need immediate attention?"**

Wait for the Genie response (10–15 sec). The agent will return a natural language answer with data table.

**SAY:**
> "The agent just queried our metric views in real time. No SQL, no dashboard switching — the planner gets an answer right where they work."

**OPTIONALLY** type a follow-up: **"How many customers are affected in Colorado?"**

**SAY:**
> "It maintains conversational context. This is the Databricks intelligence layer — Genie Spaces backed by governed metric views, embedded directly into the operational app."

---

### Scene 4: Device Detail Table (30 sec)

**SCROLL DOWN** to the Device Detail table.

**SAY:**
> "Below the map, every device is listed with its install date, alarm count, and ML risk score. The planner can sort by risk, filter by device type, and export for field crew scheduling."

**POINT TO** a high-risk device (risk score 90+).

**SAY:**
> "This CPE was installed in 2008 — 18 years old with 12 alarms. The ML model scores it at 92. That's a device we retire first."

---

### Beat 1 Transition

**SAY:**
> "So now we know WHERE the copper is and HOW BAD it is. But before we touch anything, we need to know: are we clear on regulations? Let me switch to our Regulatory Assistant."

**SWITCH** to the regulatory-assistant browser tab.

---

## BEAT 4: "Are We Clear on Regs Everywhere We Touch?" (4 min)

### App: regulatory-assistant (Regulatory Compliance Assistant)

---

### Scene 5: Regulatory Overview (45 sec)

**The audience sees** the Lakelink Fiber header ("Regulatory Assistant"), a global jurisdiction dropdown, 4 tabs (Ask / Jurisdiction Map / Checklist / Documents), and a KPI bar.

**SAY:**
> "Copper retirement isn't just an engineering problem — it's a regulatory minefield. Every state has different PUC rules, different notice periods, different customer protection requirements. This app puts 528 regulatory documents at our team's fingertips."

**POINT TO** the KPI bar:

| Card | Expected Value | Talking Point |
| --- | --- | --- |
| Documents | 528 | "528 documents indexed — FCC orders, state PUC dockets, compliance guides" |
| Jurisdictions | 7 | "6 states plus federal" |
| Federal Docs | (count) | "FCC orders and guidance at the federal level" |
| State Docs | (count) | "State-specific PUC rules and dockets" |
| Doc Types | (count) | "Multiple document categories" |
| Total Words | (count)K | "Massive corpus — no human can read all of this" |

**SAY:**
> "No human can read 528 regulatory documents. But our RAG agent can. It uses Databricks Vector Search and a foundation model to answer compliance questions with source citations."

---

### Scene 6: Ask the Regulatory Agent (90 sec)

**You are on the "Ask" tab** (default landing). The screen shows three categorized question cards: FCC Section 214, State PUC Rules, Operations & Compliance.

**CLICK** the suggested question: **"What changed with FCC 26-19?"**

Wait for RAG response (5–15 sec). The agent returns an answer with [Source N] citation links.

**SAY:**
> "FCC 26-19 is the landmark order that streamlined copper retirement. Our agent summarizes the key changes and cites the exact source documents. Watch — I can click any citation."

**CLICK** a [Source N] citation superscript. The **Citation Sidebar** slides in from the right showing the document title, type, jurisdiction, and excerpt.

**SAY:**
> "Every answer is grounded in real documents. The legal team can verify the source, read the full text, or jump to the document browser. This isn't a hallucination — it's governed RAG."

**CLOSE** the citation sidebar.

**TYPE** a follow-up question: **"What are Colorado's copper retirement requirements?"**

**SAY:**
> "Now I'm asking about state-specific rules. The agent searches across both federal AND state documents to give a complete answer. Colorado has specific PUC notice requirements that differ from Oregon."

---

### Scene 7: Jurisdiction Map (45 sec)

**CLICK** the **"Jurisdiction Map"** tab.

**SAY:**
> "The jurisdiction map gives a visual overview of compliance status across all six states. Green means clear, yellow means pending filings, red means blocked or overdue."

**HOVER** over Oregon (should show status details in tooltip).

**CLICK** on Colorado to set the jurisdiction filter.

**SAY:**
> "Clicking a state sets the global filter — every tab now shows Colorado-specific data. The checklist, the documents, even the KPIs update."

---

### Scene 8: Compliance Checklist (45 sec)

**CLICK** the **"Checklist"** tab.

**SAY:**
> "This is the compliance checklist — a hierarchical view organized by State, Wire Center, and Requirement. Each item has a status: complete, in-progress, pending, or overdue."

**EXPAND** the Colorado section (should be pre-expanded). Point to a few items.

**SAY:**
> "The operations team uses this daily. They can filter by status — show me only overdue items — or by requirement type. Every wire center has a clear punch list before we can retire copper."

**OPTIONALLY** change the status filter to show only "overdue" or "pending" items.

---

### Scene 9: Document Browser (30 sec)

**CLICK** the **"Documents"** tab.

**SAY:**
> "Finally, the document browser gives direct access to the full corpus. Filter by jurisdiction, document type, or search by keyword. Each document card shows the issuing body, effective date, and a summary."

**POINT TO** a document card (e.g., an FCC Order or a State PUC Docket).

**SAY:**
> "This is the single source of truth for regulatory compliance. It feeds the RAG agent, the checklist, and the jurisdiction map — all from one governed data layer."

---

## Closing (30 sec)

**SAY:**
> "Let me recap what we just saw:
> 
> 1. **$604 million** in annual revenue at risk across nearly 15,000 copper circuits.
> 2. A **prioritization map** powered by ML risk scoring — so we retire the right assets first.
> 3. An **embedded Genie agent** that lets non-technical planners ask questions in plain English.
> 4. A **regulatory assistant** with 528 documents, RAG-powered answers with citations, and a compliance checklist.
> 5. All of it built on **Databricks** — Unity Catalog for governance, Vector Search for retrieval, Genie for natural language, and Databricks Apps for delivery.
> 
> This is how Lakelink Fiber turns a $604M risk into a $32M EBITDA opportunity — with data."

---

## Appendix: Handling Q&A

### "Is this real data?"
> "The data is synthetic — generated to match realistic telco network patterns. But the platform, ML models, and integrations are all production-ready. In a real deployment, this connects to live OSS/BSS systems."

### "What ML model scores the risk?"
> "It's an XGBoost model trained on device age, alarm history, environmental factors, and network topology. Served via Databricks Model Serving with inference table logging for monitoring."

### "How does the Genie agent work?"
> "Genie is Databricks' natural language analytics layer. It translates questions into SQL against governed metric views. No prompt engineering needed — it understands the data model."

### "How does the regulatory RAG work?"
> "We chunk 528 regulatory documents, embed them with GTE-Large via a Vector Search index, and run retrieval-augmented generation through a foundation model API. Every answer includes source citations."

### "What's the total EBITDA impact?"
> "$32.2 million over 6 quarters in the base scenario — $31.4M in cost savings against $78.8M capex, with $27.5M net benefit. Peak migration is Q2 2027 at $9.2M EBITDA impact."

### "Why those six states?"
> "CO, MN, WA, OR, ID, AZ represent a diverse cross-section — mountain west aging plant, Pacific Northwest moisture exposure, desert heat stress, and older metro/suburban networks. Enough variety to stress-test the platform."

### "Can the Genie agent answer anything?"
> "It's scoped to the copper retirement data model — copper inventory, risk scores, revenue impact, customer impact, and EBITDA projections. It won't answer questions outside that domain."

---

## Appendix: App URLs & Technical Details

| App | Beat | URL Pattern |
| --- | --- | --- |
| copper-map | Beat 1 | https://copper-map-{workspace}.databricks.app |
| regulatory-assistant | Beat 4 | https://regulatory-assistant-{workspace}.databricks.app |

| Component | Technology |
| --- | --- |
| copper-map | Python/Dash + Plotly + Dash Bootstrap |
| regulatory-assistant | React/TypeScript + Vite + react-simple-maps |
| Data Layer | Unity Catalog (cdm_tmforum.copper_retirement) |
| ML Scoring | XGBoost via Model Serving (copper-retirement-risk) |
| Analytics Agent | Genie Space (Copper Retirement Analytics) |
| RAG Agent | Vector Search (regulatory_doc_vs_index, 528 docs) + FMAPI |
| Metric Views | project_status, customers_impacted, ebitda_achieved, ebitda_forecast |

---

*Script prepared by @app-developer · Sep 18, 2026 · Numbers frozen per DA-DEMO-NUMBERS-FINAL-0918*