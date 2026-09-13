# P7-REG — Regulatory Assistant UI: UX Backlog

**Author:** @app-developer | **Date:** 2026-09-10
**Task:** P7-REG-UX-BACKLOG (assigned by @pm 2026-09-10)
**Demo Beat:** 4 — "Are we clear on regs everywhere we touch?"
**Priority:** Thin-slice target — ships before P7-TRIAGE and P7-COMMODITY
**Framework:** AppKit (React/TypeScript), `--features analytics`
**Governance Tags:** `project: copper-retirement`, `developer: copper-app`

---

## 1. Product Context

### What the Demo Must Show

A telco executive asks: "We're retiring copper in 6 states. What are the regulatory requirements in each jurisdiction?" The P6-REG agent answers with citations to FCC orders and state PUC rules. The UI must:

1. Accept natural-language questions about copper retirement regulations
2. Display agent answers with **inline citations** to source documents
3. Let the user browse regulatory requirements by **jurisdiction** (state/federal)
4. Show a **compliance checklist** per wire-center or state
5. Surface **escalation paths** when the agent can't answer or when human review is needed

### FCC 26-19 Grounding (from BUILD-PLAN.md §0)

- Section 251(c)(5) network-change FCC filing eliminated
- Section 214(a) discontinuance streamlined (31-day auto-grants, blanket grandfathering)
- **Section 214 authorization still required** for service discontinuance
- 90-day residential direct-notice requirement remains
- The UI must reflect these corrected facts — Demo Beat 4 is a headline screen

---

## 2. Screens & Navigation

### Screen Map (4 screens, single-page app with tab navigation)

```
┌─────────────────────────────────────────────────────┐
│  [Ask]  [Jurisdiction Map]  [Checklist]  [Documents] │
├─────────────────────────────────────────────────────┤
│                                                     │
│              Active Screen Content                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Screen 1: Ask (default landing)
**Purpose:** Chat interface to P6-REG agent — the primary interaction surface.

| Component | Description | Complexity |
|---|---|---|
| `RegAgentChat` | Full-height chat panel. User types questions, agent responds with structured answers + citations. SSE streaming for real-time token display. | HIGH |
| `CitationSidebar` | Right-side panel that opens when user clicks a citation link. Shows document excerpt with highlighted passage. | MEDIUM |
| `SuggestedQuestions` | Pre-loaded question chips for cold-start: "What's the Section 214 process for TX?", "90-day notice requirements?", "State PUC filing deadlines?" | LOW |
| `JurisdictionContext` | Sticky header showing active jurisdiction filter (e.g., "Showing: Texas" or "All States"). Clicking opens jurisdiction selector. | LOW |

#### Screen 2: Jurisdiction Map
**Purpose:** Geographic overview of regulatory landscape across Lakelink's footprint.

| Component | Description | Complexity |
|---|---|---|
| `JurisdictionMap` | US state map (choropleth, not deck.gl H3 — different from P7-MAP). Color by compliance status: green (clear), yellow (pending), red (blocked). Click state to filter. | MEDIUM |
| `StateRegCard` | Click-on-state detail card: regulator name, notice period, filing type, Section 214 required, contacts, pending deadlines. | MEDIUM |
| `JurisdictionTable` | Tabular alternative to map: state, federal_regulator, state_puc, notice_period_days, filing_type, section_214_required, residential_notice_days, status. Sortable/filterable. | LOW |
| `RegKPIs` | Top bar: jurisdictions covered, pending filings, days until next deadline, compliance % | LOW |

#### Screen 3: Checklist
**Purpose:** Per-wire-center or per-state regulatory compliance tracking.

| Component | Description | Complexity |
|---|---|---|
| `ComplianceChecklist` | Hierarchical checklist: State → Wire Center → Requirement → Status. Expandable tree view. Requirements: notice sent, waiting period elapsed, approval received, 911 coordination complete, etc. | HIGH |
| `ChecklistFilters` | Filter by: state, status (pending/complete/overdue/blocked), requirement type (Section 214, state PUC, 911, residential notice). | LOW |
| `DeadlineTimeline` | Horizontal timeline of upcoming regulatory deadlines across all jurisdictions. Highlights overdue items in red. | MEDIUM |
| `EscalationBanner` | Alert banner when checklist items are overdue or approaching deadline. "Escalate to legal" button. | LOW |

#### Screen 4: Documents
**Purpose:** Browse and search the regulatory document corpus.

| Component | Description | Complexity |
|---|---|---|
| `DocumentBrowser` | Searchable list of FCC orders, state PUC dockets, notice templates. Filter by document_type, jurisdiction, date range. | MEDIUM |
| `DocumentViewer` | PDF/text rendering panel with citation highlighting. When opened from a chat citation, scrolls to the relevant passage. | HIGH |
| `DocumentMetadata` | Sidebar: title, date, issuing body, effective dates, related policies, keywords. | LOW |

---

## 3. Citation Display Design

### Requirements

The regulatory assistant's credibility depends on traceable citations. Every agent answer must show where the information comes from.

### Citation Format

```
Agent response text here. Under FCC 26-19, the Section 214(a) discontinuance
process has been streamlined to include 31-day automatic grants for qualifying
applications. [1]

───────────────────────────────
[1] FCC 26-19, "Accelerating Wireline Broadband Deployment", para. 47-52
    Effective: 2026-04-15 | Jurisdiction: Federal
    ▸ View source document
```

### Citation Components

| Element | Implementation |
|---|---|
| **Inline marker** | Superscript numbered link `[1]` in chat message. Clickable → opens CitationSidebar. |
| **Citation footer** | Below each agent response: numbered list with document title, paragraph/section reference, effective date, jurisdiction scope. |
| **Source preview** | CitationSidebar shows 200-word excerpt from source document with the cited passage highlighted in yellow. |
| **Full document link** | "View source document" navigates to Documents screen with doc pre-selected. |
| **Confidence indicator** | Agent-provided confidence score (high/medium/low). Low confidence triggers escalation affordance. |
| **Staleness warning** | If cited document's effective_end_date < today, show amber warning: "This regulation may have been superseded." |

### Data Flow for Citations

```
User question
    → P6-REG agent (Model Serving endpoint)
    → Agent searches Lakebase vector index (P5-SEARCH) over regulatory corpus
    → Returns: answer_text + citations[{doc_id, passage, paragraph_ref, confidence}]
    → UI renders answer with inline citation markers
    → Click citation → CitationSidebar fetches document chunk from corpus
```

**Thin-slice fallback (before P6-REG exists):** Mock agent responses as static JSON. Pre-write 10-15 Q&A pairs covering key FCC 26-19 topics (Section 214 streamlining, 90-day notice, 911 coordination, state PUC variations). Citations reference mock documents.

---

## 4. Jurisdiction Filters

### Filter Dimensions

| Filter | Source | Values |
|---|---|---|
| **State** | `tmf_enterprise.regulator.jurisdiction` + synthetic `state_puc_requirements` | 6 LEGACY_STATES (CO, WA, OR, AZ, MN, ID) + Federal |
| **Regulator type** | `regulator.type` | federal, state_puc, municipal |
| **Compliance status** | Computed from checklist | clear, pending, blocked, overdue |
| **Requirement type** | Synthetic `regulatory_requirements_by_jurisdiction` | section_214, state_puc_filing, residential_notice, 911_coordination, environmental |
| **Document type** | `tmf_shared.document.type` filtered | fcc_order, puc_docket, notice_template, guidance, legislative |
| **Effective date range** | `policy.effective_start_date` / `effective_end_date` | Date picker |

### Filter Behavior

- **Global filter** (JurisdictionContext header): persists across all 4 screens. Setting state = "Texas" filters Ask screen suggestions, Jurisdiction Map highlights TX, Checklist shows TX items, Documents shows TX-relevant docs.
- **Local filters** (per-screen): additive to global filter. E.g., Checklist screen can further filter by status=overdue within the globally-selected state.
- **Ask screen**: jurisdiction filter pre-populates agent context. Agent receives `{jurisdiction: "TX"}` as context parameter so answers are state-scoped.

---

## 5. Escalation Affordances

### Escalation Triggers

| Trigger | Condition | UI Affordance |
|---|---|---|
| **Agent uncertainty** | Agent returns confidence < 0.6 or says "I'm not sure" | Amber banner: "This answer has low confidence. Consider verifying with legal." + "Escalate" button |
| **No answer** | Agent cannot find relevant citations | Red banner: "No regulatory guidance found for this query." + "Request legal review" button |
| **Overdue checklist item** | Checklist item past deadline | Red row highlight + "Escalate to legal" action in row context menu |
| **Conflicting regulations** | Agent detects federal vs state conflict | Orange banner: "Potential regulatory conflict detected between federal and state requirements." + "Flag for review" button |
| **Document staleness** | Cited document expired (effective_end_date < today) | Amber citation warning + "Check for updates" link |

### Escalation Actions

| Action | Behavior |
|---|---|
| **Escalate to legal** | Creates a structured escalation record: question, agent answer, confidence, citations, jurisdiction. In thin-slice: opens a modal showing the escalation payload. In production: writes to Lakebase `regulatory_escalations` table + sends notification. |
| **Request legal review** | Same as escalate but with priority flag. |
| **Flag for review** | Adds a review tag to the checklist item. Visible in Checklist screen filter (status=flagged). |
| **Human override** | Authorized user can mark a checklist item as "manually verified" with a note. Overrides agent assessment. Audit-logged. |

### Escalation UI Pattern

```
┌──────────────────────────────────────────────────┐
│ ⚠ Low Confidence Answer                          │
│                                                  │
│ The agent's response about [topic] has low       │
│ confidence (0.45). This may require verification │
│ by the legal/regulatory team.                    │
│                                                  │
│ [Escalate to Legal]  [Accept Anyway]  [Dismiss]  │
└──────────────────────────────────────────────────┘
```

---

## 6. Data Dependencies & Source Strategy

### Available NOW (real data — can power thin-slice)

| Table | Rows | What It Provides | UX Surface |
|---|---|---|---|
| `tmf_marketsales.policy` | 10K (5,065 reg-flagged) | Policy types, status, geographic_scope, enforcement_mode | JurisdictionTable, filters |
| `tmf_marketsales.policy_rule` | 100K (50,190 reg-flagged) | Executable rules with conditions, thresholds, rule_category | ComplianceChecklist requirements |
| `tmf_marketsales.policy_condition` | 1K | Policy conditions | Checklist condition details |
| `tmf_enterprise.regulator` | 1K (133 active) | Jurisdiction, authority_level, contacts, website | StateRegCard, JurisdictionTable |
| `tmf_shared.document` | 10K (1,679 legal/reg) | Document metadata, file_type, classification | DocumentBrowser, DocumentMetadata |
| `revenue_assurance.silver_doc_intelligence_contracts` | 50 | AI-parsed contract intelligence (reusable pattern) | Proof of document parsing capability |

**Caveat:** All text field values in these tables are synthetic hashes (e.g., `"7RQU874899UG"`). The schema structure is usable for layout and filter design, but display values will need either (a) the PROFILE-POLICY-RULES output from @data-analyst confirming which columns have meaningful values, or (b) mock overlay for demo.

### Blocked — Needs Synthesis (P0-DATAGEN-REG)

| Data Gap | What P7-REG Needs | Blocking Task |
|---|---|---|
| State PUC jurisdiction requirements | Per-state notice periods, filing types, deadlines | P0-DATAGEN-REG |
| Section 214/notice-period lookup | Federal requirement reference table | P0-DATAGEN-REG |
| FCC order/docket text corpus | Full-text documents for RAG and DocumentViewer | P1-REG |
| `regulatory_requirements_by_jurisdiction` gold table | Compliance checklist source of truth | P3-GOLD |

### Decision Gate: P0-DATAGEN-REG vs PROFILE-POLICY-RULES

> **RESOLVED 2026-09-12** — @data-planner confirmed all policy/rule text is 100% hashes. Full synthesis via P0-DATAGEN-REG is mandatory.

@data-analyst `PROFILE-POLICY-RULES` task will determine whether the 110K rows in `policy` + `policy_rule` contain **meaningful regulatory content** or are entirely synthetic hashes. This decision affects P7-REG UX:

| If PROFILE-POLICY-RULES finds... | Impact on P7-REG |
|---|---|
| **Meaningful rule content** (real-looking descriptions, conditions, jurisdiction references) | JurisdictionTable + ComplianceChecklist can use real data. P0-DATAGEN-REG scope reduces significantly. Thin-slice accelerates. |
| **All synthetic hashes** (no usable text content) | Full mock data layer needed. P0-DATAGEN-REG must synthesize realistic regulatory requirements. Thin-slice uses hardcoded mock JSON. |

**Recommendation:** Design the app with a `USE_MOCK_DATA` feature flag (same pattern as P7-MAP). Build the mock layer now; swap to real data when available.

---

## 7. Thin-Slice Mock Flow (ships FIRST)

### Goal

A clickable demo of Demo Beat 4 that works **before P6-REG agent, P0-DATAGEN-REG, or P1-REG exist**. Uses hardcoded mock data grounded in real FCC 26-19 facts from BUILD-PLAN.md §0.

### Mock Data Spec

#### 7.1 Mock Agent Q&A Pairs (15 pairs)

| # | Question | Key Answer Points | Citations |
|---|---|---|---|
| 1 | "What is Section 214?" | Section 214(a) of Communications Act — authorization required to discontinue service. FCC 26-19 streamlined: 31-day auto-grants, consolidated tech-transition rule. | FCC 26-19 para. 47-52 |
| 2 | "Do we still need Section 214 authorization?" | YES — still required when copper retirement causes service discontinuance. FCC 26-19 eliminated Section 251(c)(5) filing, NOT Section 214. | FCC 26-19 para. 23-31 |
| 3 | "What notice do we give residential customers?" | 90-day direct notice to affected residential customers. Required even under streamlined rules. | FCC 26-19 para. 55-58, 47 CFR §63.71 |
| 4 | "What changed with FCC 26-19?" | Eliminated Section 251(c)(5) network-change FCC filing. Streamlined 214(a): 31-day auto-grants, blanket grandfathering, added 911 coordination. | FCC 26-19 full order |
| 5 | "What are Colorado's requirements?" | Colorado PUC (CPUC) requires 90-day notice aligned with federal baseline, broadband availability certification in retirement area, and rural service continuity plan. Lifeline transition coordination required. | 4 CCR 723-2-XXX |
| 6 | "911 coordination requirements?" | FCC 26-19 added 911-coordination requirement. Must notify PSAPs and coordinate with 911 authorities before copper retirement in area. | FCC 26-19 para. 62-67 |
| 7 | "What's the timeline for copper retirement in Oregon?" | Oregon PUC requires 120-day advance notice (longer than federal 90-day). Environmental impact assessment for rural areas. | OAR 860-023-0XXX |
| 8 | "Can we retire mid-contract?" | No — active MSA/contract constrains timing. Must wait for contract expiration or negotiate early termination. Check `ironclad_clm_source.contract_record` for active contracts. | Contract terms + FCC guidance |
| 9 | "What about wholesale/reseller customers?" | Different notice requirements for wholesale vs retail. Wholesale: 180-day notice per interconnection agreements. Retail: 90-day per FCC 26-19. | FCC 26-19 para. 71-75, ICA terms |
| 10 | "Environmental requirements for underground copper?" | Varies by state. CO: CPUC notification. OR: DEQ notification. AZ: minimal. Federal: no blanket EPA requirement for copper removal. | State-specific environmental regs |
| 11 | "What is blanket grandfathering authority?" | FCC 26-19 grants carriers blanket authority to grandfather copper services — can transition customers to equivalent service without individual tariff filings. | FCC 26-19 para. 38-42 |
| 12 | "Notice requirements for Idaho?" | Idaho PUC follows federal baseline: 90-day residential notice, Section 214 when applicable. No additional state-specific copper retirement rules as of 2026. | IDAPA 31.XX.XX |
| 13 | "Arizona PUC requirements?" | ACC (Arizona Corporation Commission): 90-day notice aligned with federal. Requires alternative service plan filed 60 days before retirement date. | AAC R14-2-XXX |
| 14 | "Minnesota regulatory landscape?" | MN PUC: 120-day advance notice. Requires broadband availability certification in retirement area. Cold-weather service continuity rules apply. | Minn. Rules 7812.XXXX |
| 15 | "What's the process to start retirement in Washington?" | WUTC: File notice 90 days in advance. Requires 911 coordination certificate. Customer migration plan must demonstrate equivalent service availability. | WAC 480-120-XXX |

#### 7.2 Mock Jurisdiction Data (6 states + Federal)

| Jurisdiction | Regulator | puc_notice_days | Filing Type | Section 214 Required | residential_notice_days | Special Requirements |
|---|---|---|---|---|---|---|
| Federal | FCC | 90 days | Section 214(a) | Yes (when discontinuance) | 90 days direct | 911 coordination, blanket grandfathering |
| Colorado | CPUC | 90 days | CPUC Filing + 214 | Yes | 90 days | Broadband availability certification, rural service continuity |
| Washington | WUTC | 90 days | WUTC Filing + 214 | Yes | 90 days | 911 coordination certificate, migration plan |
| Oregon | OPUC | 120 days | OPUC Filing + 214 | Yes | 120 days | Rural environmental assessment, extended notice |
| Arizona | ACC | 90 days | ACC Filing + 214 | Yes | 90 days | Alternative service plan (60 days before) |
| Minnesota | MN PUC | 120 days | MN PUC Filing + 214 | Yes | 120 days | Broadband availability cert, cold-weather rules |
| Idaho | IPUC | 90 days | Federal baseline | Yes | 90 days | No additional state requirements |

#### 7.3 Mock Documents (8 documents)

| Doc ID | Title | Type | Jurisdiction | Effective Date |
|---|---|---|---|---|
| DOC-001 | FCC 26-19: Accelerating Wireline Broadband Deployment | fcc_order | Federal | 2026-04-15 |
| DOC-002 | 47 CFR §63.71 — Procedures for Discontinuance | federal_regulation | Federal | 2024-01-01 |
| DOC-003 | Section 214(a) Streamlined Application Guide | guidance | Federal | 2026-05-01 |
| DOC-004 | CPUC Network Retirement Notice Requirements | puc_docket | Colorado | 2025-08-01 |
| DOC-005 | Oregon PUC Copper Retirement Notice Requirements | puc_docket | Oregon | 2025-03-15 |
| DOC-006 | MN PUC Cold-Weather Service Continuity Standards | puc_docket | Minnesota | 2024-11-01 |
| DOC-007 | 911 Coordination Requirements for Network Transitions | guidance | Federal | 2026-04-15 |
| DOC-008 | Blanket Grandfathering Authority — Implementation Guide | guidance | Federal | 2026-06-01 |

#### 7.4 Mock Compliance Checklist (per state)

| Step | Requirement | Federal Basis | Typical Status |
|---|---|---|---|
| 1 | Identify affected services | Section 214(a) | complete |
| 2 | Determine if discontinuance applies | Section 214(a) | complete |
| 3 | File Section 214 application (if required) | FCC 26-19 | pending |
| 4 | Send 90-day residential direct notice | 47 CFR §63.71 | not_started |
| 5 | State PUC filing (if required) | State-specific | not_started |
| 6 | 911/PSAP coordination | FCC 26-19 | not_started |
| 7 | Environmental review (if required) | State-specific | not_applicable |
| 8 | Wait for 31-day auto-grant (or approval) | FCC 26-19 | blocked |
| 9 | Execute customer migration | Carrier process | not_started |
| 10 | File completion notice | FCC + state | not_started |

---

## 8. SQL Queries (config/queries/)

All queries include `USE_MOCK_DATA` fallback. When mock is disabled, these hit the catalog.

| # | File | Purpose | Source Tables |
|---|---|---|---|
| 1 | `reg_kpis.sql` | Summary KPIs: jurisdictions, pending filings, next deadline, compliance % | Synthetic `regulatory_requirements_by_jurisdiction` OR mock |
| 2 | `jurisdiction_summary.sql` | Per-state regulatory summary for JurisdictionTable | `tmf_enterprise.regulator` + synthetic requirements |
| 3 | `compliance_checklist.sql` | Hierarchical checklist data: state → wire_center → requirement → status | Synthetic `regulatory_checklist_status` (P5-SCHEMA) OR mock |
| 4 | `document_search.sql` | Parameterized doc search by type, jurisdiction, keyword | `tmf_shared.document` (filtered to legal/regulatory) |
| 5 | `policy_rules_by_jurisdiction.sql` | Active regulatory policy rules grouped by geographic_scope | `tmf_marketsales.policy` + `policy_rule` WHERE regulatory_compliance_flag = true |
| 6 | `escalation_summary.sql` | Open escalations: count by state, priority, age | Lakebase `regulatory_escalations` OR mock |
| 7 | `deadline_timeline.sql` | Upcoming deadlines sorted by date | Synthetic requirements + checklist |

---

## 9. Component Inventory Summary

| Screen | Components | Complexity | Data Status |
|---|---|---|---|
| Ask | RegAgentChat, CitationSidebar, SuggestedQuestions, JurisdictionContext | HIGH | Mock (agent not built) |
| Jurisdiction Map | JurisdictionMap, StateRegCard, JurisdictionTable, RegKPIs | MEDIUM | Partial (regulator table available, jurisdiction lookup blocked) |
| Checklist | ComplianceChecklist, ChecklistFilters, DeadlineTimeline, EscalationBanner | HIGH | Mock (checklist table not built) |
| Documents | DocumentBrowser, DocumentViewer, DocumentMetadata | MEDIUM | Partial (document table available, FCC corpus blocked) |

**Total: 15 React components, 7 SQL queries**

---

## 10. Dependencies on Other Agents

| Dependency | Agent | Status | Impact on P7-REG |
|---|---|---|---|
| P6-REG agent endpoint | @ml-engineer / agent team | NOT STARTED | Chat interface is mock until agent exists |
| P0-DATAGEN-REG | @data-engineer | NOT STARTED (waiting on PROFILE-POLICY-RULES) | Jurisdiction lookup + checklist source data |
| PROFILE-POLICY-RULES | @data-analyst | NOT STARTED | Determines if real policy data is usable or mock needed |
| P3-GOLD `regulatory_requirements_by_jurisdiction` | @data-engineer | NOT STARTED | Gold table powering jurisdiction summary + checklist |
| P5-SCHEMA Lakebase `regulatory_checklist_status` | @data-engineer | NOT STARTED | Write-back for checklist status updates |
| P5-SEARCH regulatory corpus vector index | @data-engineer | NOT STARTED | Agent RAG retrieval backend |
| P1-REG FCC document corpus | @data-engineer | NOT STARTED | Full-text documents for DocumentViewer |
| FIX-COORDINATES | CEO (manual run) | BLOCKED | Jurisdiction Map geo rendering |

---

## 11. Scaffold Plan (what to build NOW)

### Phase A: Thin-Slice Scaffold (2 days)

Build a working demo with mock data that tells the regulatory story:

1. **AppKit init** — `databricks apps init regulatory-assistant --features analytics`
2. **Mock data layer** — `mock/mockData.ts` with all 7.1-7.4 mock data
3. **Ask screen** — RegAgentChat with mock streaming responses, CitationSidebar, SuggestedQuestions
4. **Jurisdiction Map screen** — Static US choropleth (6 LEGACY_STATES highlighted), JurisdictionTable with mock data
5. **RegKPIs** — Hardcoded KPIs from mock jurisdiction data
6. **Feature flag** — `USE_MOCK_DATA=true` in environment config

### Phase B: Live Data Integration (2 days, after dependencies land)

1. **SQL queries** — Wire up all 7 queries to real tables
2. **Agent integration** — Connect RegAgentChat to P6-REG Model Serving endpoint via SSE
3. **Checklist screen** — Connect to `regulatory_checklist_status` Lakebase table
4. **Documents screen** — Connect DocumentViewer to real FCC corpus
5. **Escalation write-back** — Connect to Lakebase `regulatory_escalations` table

### Phase C: Polish (1 day)

1. **Playwright tests** — Smoke tests for all 4 screens
2. **Error states** — Loading, empty, and error states for all data-driven components
3. **Responsive layout** — Ensure chat + citation sidebar work on demo-day screen resolution
4. **DAB config** — Add app resource to `bundle/databricks.yml` with governance tags

**Estimated total: 5 days (Phase A can ship immediately for thin-slice demo)**

---

## 12. File Structure

```
apps/regulatory-assistant/
├── REG_UX_BACKLOG.md          # This document
├── app.yaml                   # Databricks App config (Phase A)
├── src/
│   ├── App.tsx                # Root with tab navigation
│   ├── pages/
│   │   ├── AskPage.tsx        # Ask screen
│   │   ├── JurisdictionPage.tsx  # Jurisdiction Map screen
│   │   ├── ChecklistPage.tsx  # Checklist screen
│   │   └── DocumentsPage.tsx  # Documents screen
│   ├── components/
│   │   ├── RegAgentChat.tsx
│   │   ├── CitationSidebar.tsx
│   │   ├── SuggestedQuestions.tsx
│   │   ├── JurisdictionContext.tsx
│   │   ├── JurisdictionMap.tsx
│   │   ├── StateRegCard.tsx
│   │   ├── JurisdictionTable.tsx
│   │   ├── RegKPIs.tsx
│   │   ├── ComplianceChecklist.tsx
│   │   ├── ChecklistFilters.tsx
│   │   ├── DeadlineTimeline.tsx
│   │   ├── EscalationBanner.tsx
│   │   ├── DocumentBrowser.tsx
│   │   ├── DocumentViewer.tsx
│   │   └── DocumentMetadata.tsx
│   ├── mock/
│   │   └── mockData.ts        # All mock data from §7
│   └── lib/
│       ├── formatters.ts      # Date, status, citation formatters
│       └── types.ts           # TypeScript interfaces
├── config/
│   └── queries/
│       ├── reg_kpis.sql
│       ├── jurisdiction_summary.sql
│       ├── compliance_checklist.sql
│       ├── document_search.sql
│       ├── policy_rules_by_jurisdiction.sql
│       ├── escalation_summary.sql
│       └── deadline_timeline.sql
├── server/
│   └── server.ts              # Analytics plugin
└── tests/
    └── smoke.spec.ts          # Playwright smoke tests
```

---

## 13. Open Questions for @pm

1. **Lakebase write-back for checklist:** Should checklist status changes write to Lakebase (adds P5-SCHEMA dependency) or just be read-only for thin-slice?
2. **Escalation destination:** Where do escalated items go? Email notification? Slack? Lakebase table only? Need to define for Phase B.
3. **Document rendering:** Real FCC PDFs vs synthetic text? If synthetic, @data-engineer needs guidance on document format for P0-DATAGEN-REG.
4. **Agent chat vs Genie plugin:** Should RegAgentChat use a custom SSE endpoint or the AppKit Genie plugin? Depends on how P6-REG is served.
5. **Choropleth library:** JurisdictionMap needs a US state choropleth (not H3 hex like P7-MAP). Recommend `react-simple-maps` or D3 `topojson`. Confirm library choice.
