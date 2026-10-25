# Copper Retirement Solution Accelerator — Partner Playbook (DRAFT v0.6)

> Owner: @pm. Task: ACC-DOCS-PARTNER-PLAYBOOK. Status: DRAFT v0.6 (2026-10-25 05:10 UTC). v0.6 adds §6a, a static fresh-workspace dependency inventory: what a clean `bundle deploy -t partner` needs before the pipeline and app can run. It is a desk check, not a live fresh deploy (that is COO-Q-20261024-1800-3 / ACC-QA-FRESH-DEPLOY). Earlier: v0.5 (2026-10-25 00:30 UTC). v0.5 applies the @qa ACC-QA-DEF-PB-V04 fixes: the jurisdiction matrix is live, the Regulatory tab answers are citable through interim Delta retrieval, the §5 demo script now uses the unified app, the app count is current, and the corpus is 1,598 real chunks. v0.4 restated the §3 value case: the $43.3M salvage headline is withdrawn and replaced by an opex-led, cited value case (COO-Q-20261024-1800-2, ACC-PM-PLAYBOOK-ROI-RESTATE). It also applies the @qa ACC-QA-DEF-PB-V03 fixes (VS endpoint/model, §8 cost, stale 811 text, ID ticket life, subsection URLs). v0.3 rebuilt the §2a 811 table from verified statute text. Sections 5-7 now absorb DEMO-RUNBOOK.md, DEMO-ROLLBACK-RECOVERY.md, DEMO-ENV-FREEZE-CHECKLIST.md and demo_kpi_cheat_sheet.md (content merged 2026-10-24; the 4 source files are **not yet deleted**. Workspace deletion by a scheduled agent was blocked, so it is pending CEO approval. Originals are also in git history on origin/main of github.com/skhage/copper-retirement, commits a6aa6d0 and 946b559). README.md is kept as the repo root readme and now points here.
>
> Rule for this document: every regulatory statement carries an official URL. Anything not yet verified is marked **GAP** and is not to be presented to a customer as fact. Durations are planning assumptions for SOW sizing, not regulatory requirements, and must be validated by the partner's field-operations lead.

## 0. Data disclosure
The demo dataset (Lakelink Fiber) is **synthetic**. Device, customer, wire-center, contractor and dig-incident data are generated. Regulatory content is being replaced with real downloaded sources (R1). Status as of 2026-10-25: `regulatory_doc_chunks` holds **1,598 real chunks from 32 official sources** (37 distinct official URLs, 0 rows without a `source_url`), plus 528 legacy chunks flagged `is_synthetic = true`. The unified app's **Regulatory tab answers only from the real chunks** (`is_synthetic = false`). Each answer carries [S#] chips that link to the official URL, and the tab replies "No official source found" when nothing matches. @qa found 20 of 20 sampled answers cited real URLs. Retrieval currently runs through the interim Delta function `cdm_tmforum.copper_retirement.search_regulatory_chunks(query, k)` (bge-large cosine search, returns `source_url` on every row). The VS index `regulatory_doc_chunks_vs_index` still serves the 528 synthetic chunks until the same-name recreate (ACC-VS-INDEX-RECREATE, CEO action) and re-sync (ACC-REG-VS-RESYNC). Until then, do not point any client at the VS index directly. Copper price is now a real public series: IMF Primary Commodity Prices, copper (PCOPPUSDM, monthly, USD/metric ton) in `cdm_tmforum.copper_retirement.copper_commodity_price_official` (417 rows; `source_url` = https://fred.stlouisfed.org/series/PCOPPUSDM). LME (https://www.lme.com/en/metals/non-ferrous/lme-copper) is licensed and kept as a reference only. Copper volumes, plant, customers and costs remain **synthetic**.

## 1. Accelerator roadmap

| Release | Scope | Exit criteria | Target date |
| --- | --- | --- | --- |
| R1 — Real regulatory data + consolidation | Source register, downloads to `/Volumes/cdm_tmforum/copper_retirement/regulatory_source_docs`, re-chunk into `regulatory_doc_chunks`, re-sync existing VS index, retire synthetic regulatory docs, cited jurisdiction matrix; asset baseline; scratch/agent notebooks consolidated | 100% of jurisdiction rows and RAG answers carry a verified official URL; `asset_ledger_balance.rule_surplus >= 0` with notebooks reduced | 2026-11-06 |
| R2 — One unified app | `retirement-plan` evolved into tabbed accelerator app (Map/Risk, Plan, Dig Triage, Regulatory, Commodity) with shared design tokens; 4 old apps stopped/deleted | 2 apps total (accelerator + copper-task-board); WCAG AA pass by @designer | 2026-11-20 |
| R3 — Partner packaging | One-command DAB deploy with variables; this playbook complete (discovery, SOW template, ROI calculator, demo script); model card; fresh-deploy smoke test | @qa fresh-deploy passes with zero manual steps beyond documented variables | 2026-12-04 |

Critical path: ACC-REG-SOURCE-REGISTER -> ACC-REG-DOWNLOAD -> ACC-REG-PARSE-INDEX -> ACC-REG-JURISDICTION-MATRIX -> ACC-APP-PORT-REG -> ACC-QA-REG-CITATIONS; in parallel ACC-APP-IA -> ACC-APP-UNIFY-SHELL -> ports; ACC-ASSET-BASELINE -> ACC-DAB-ONE-COMMAND -> ACC-QA-FRESH-DEPLOY.

## 2. SOW phase template — copper retirement / copper harvesting

Durations are per wave of roughly 1-3 wire centers and are **planning assumptions** to be calibrated in discovery.

| # | Phase | Typical duration (assumption) | Partner / carrier roles | Deliverables | Regulatory step and official source |
| --- | --- | --- | --- | --- | --- |
| 1 | Assess and baseline | 3-4 weeks | Partner data engineer, data scientist, carrier network planning | Copper plant inventory in UC, risk scores (`copper-retirement-risk` template retrained on carrier data), customer impact, value baseline | None (internal) |
| 2 | Wave planning | 2-3 weeks | Partner PM, carrier engineering + regulatory affairs | Retirement waves, customer migration plan, jurisdiction requirements matrix per wave | Jurisdiction matrix: `cdm_tmforum.copper_retirement.jurisdiction_requirements_cited` (68 rows; 47 verified: 37 `VERIFIED_STATUTE_TEXT` and 10 `VERIFIED_OFFICIAL_PAGE`, each with `official_url`), shown in the unified app Regulatory tab. **GAP** for the other 21 rows (12 `NOT_FOUND`, 6 `STATE_GAP`, 2 `UNVERIFIED`, 1 `UNVERIFIED_CONFLICT`). Do not present those rows as fact (ACC-DP-JUR-NOTFOUND, ACC-QA-DEF-JUR-URL) |
| 3 | Regulatory notices and filings | Driven by notice periods (see source) | Carrier regulatory affairs, counsel | Copper retirement direct notices, Section 214 discontinuance application where service is discontinued, state filings | Direct notice of planned copper retirement at least 90 days before implementation (15 days if the copper serves no customers): FCC 26-19 (adopted 2026-03-26, published 91 FR 20913, 2026-04-20), Appendix A, revised 47 CFR 51.333(a)(2) — https://docs.fcc.gov/public/attachments/FCC-26-19A1.pdf . FCC 26-19 eliminates the FCC filing and Bureau public-notice/objection process for copper retirements; the ILEC still posts public notice and gives direct notice. Section 214 discontinuance: 47 CFR 63.71 — https://www.ecfr.gov/current/title-47/section-63.71 ; FCC 26-19 applies a 31-day automatic grant period to all discontinuance applications (Section III.B). **Effectiveness:** the order said these amendments (51.329, 51.333, 63.60, 63.62, 63.63, 63.71, 63.602) would not take effect until OMB PRA review (para 120). WCB announced OMB approval (control nos. 3060-0149, 3060-0741) and the amendments are **effective 2026-10-15**: 91 FR 62334, FR Doc. 2026-20192, published 2026-10-01 — https://www.federalregister.gov/documents/2026/10/01/2026-20192/wc-docket-nos-25-208-25-209-fcc-26-19-fr-id-370342-reducing-barriers-to-network-improvements-and (verified via federalregister.gov API, `effective_on` = 2026-10-15, on 2026-10-24). Notices served before 2026-10-15 fall under the prior rules (FCC 17-154 https://docs.fcc.gov/public/attachments/FCC-17-154A1_Rcd.pdf , FCC 18-74 https://docs.fcc.gov/public/attachments/FCC-18-74A1_Rcd.pdf ). **GAP:** eCFR may lag the amendment, so check the current eCFR text before quoting rule wording; state notice requirements per state |
| 4 | Customer migration | Parallel to phase 3, 6-12 weeks | Carrier care/sales, field install | Customers migrated to fiber/alternative service, migration KPI tracking | Customer notice obligations tied to discontinuance — see 47 CFR 63.71 above; state consumer rules **GAP** |
| 5 | Permits and right-of-way | 2-8 weeks, jurisdiction dependent | Partner permitting coordinator, carrier outside-plant | ROW / municipal permits, traffic control plans | Utilities on federal-aid highway ROW: 23 CFR Part 645 — https://www.ecfr.gov/current/title-23/chapter-I/subchapter-G/part-645 . Municipal permit rules **GAP** (local) |
| 6 | 811 locates and dig safety (buried plant) | Wait period set by state one-call law, plus ticket renewals per wave | Excavation contractor, carrier locate coordinator | One-call tickets per work area, positive response confirmation, dig-triage risk scoring (Dig Triage tab) | Locate underground installations before excavation: OSHA 29 CFR 1926.651(b) — https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.651 . Use one-call and wait for marks before excavating near pipelines: PHMSA 49 CFR Part 196 — https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-D/part-196 ; state damage-prevention programs: 49 CFR Part 198 — https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-D/part-198 . Industry practice: CGA Best Practices v21 — https://bestpractices.commongroundalliance.com/Portals/1/Best%20Practices%20Guide%20Version%2021%20PDF%20Download.pdf . Excavation protection: OSHA 29 CFR 1926 Subpart P (1926.651 above). Per-state notice, tolerance and ticket life: see §2a (sourced from `regulatory_source_register`; WA, AZ, CO, MN and ID are `verified_statute_text`; OR is `unverified_conflict` on ticket life) |
| 7 | Lead-sheathed cable assessment and handling | 1-3 weeks per wave (sampling, plan) | Environmental consultant, safety officer, removal contractor | Lead-sheath inventory flag per span, worker exposure plan, handling and disposal plan | Worker lead exposure in construction: OSHA 29 CFR 1926.62 — https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.62 . EPA has run response actions on lead telecom cable (Louisiana Lead Cable site) — https://response.epa.gov/site/site_profile.aspx?site_id=16204 . Scrap metal recycling exclusions under RCRA: 40 CFR 261.4 and 261.6 — https://www.ecfr.gov/current/title-40/chapter-I/subchapter-I/part-261/section-261.4 , https://www.ecfr.gov/current/title-40/chapter-I/subchapter-I/part-261/section-261.6 . **GAP:** applicability of the scrap-metal exclusion to lead-sheathed cable and state disposal rules must be confirmed by environmental counsel |
| 8 | Field removal — aerial vs buried | 4-12 weeks per wave | Removal contractor, carrier outside-plant inspector | Spans removed, pole attachments cleared, restoration sign-off | Telecom worker safety (incl. aerial work): OSHA 29 CFR 1910.268 — https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.268 . Pole-attachment / joint-use agreements **GAP** (contractual) |
| 9 | Salvage, chain of custody and sale | 2-6 weeks per wave | Salvage buyer, carrier asset recovery, finance | Weighed lots, chain-of-custody records, buyer settlement vs reference price, recovery report | Reference price: LME copper (https://www.lme.com/en/metals/non-ferrous/lme-copper, licensed data). State scrap-metal dealer and record-keeping laws **GAP** |
| 10 | Decommission and close-out | 2-4 weeks | Partner PM, carrier finance | Inventory/records retired, opex and real-estate savings booked, value report from partner value metric view | None (internal) |

Validation status: drafted by @pm from official sources above on 2026-10-24. **Not yet validated by a carrier or partner field-operations SME.** CEO was asked to name a reviewer on 2026-10-24 (status_updates id 113); no reviewer named as of 2026-10-24 09:00 UTC. Re-asked in today's rollup.

### 2a. 811 one-call requirements — footprint states (planning use only)

Source: `cdm_tmforum.copper_retirement.regulatory_source_register` (`topic = 'one_call_811'`), refreshed by @data-planner on 2026-10-24 11:24 UTC. Five states are now `verified_statute_text` (the statute text was opened and quoted, with subsection cites). Oregon is `unverified_conflict` on ticket life. Planning use only until @qa clears ACC-QA-REG-CITATIONS. v0.3 corrections: AZ hand-dig zone is 24 in, not 18 in. The MN "6 months with refresh" claim is removed because it was not verified.

| State | register source_id | Statute (official URL) | Notice before digging | Tolerance zone | Ticket / mark life | Open item |
| --- | --- | --- | --- | --- | --- | --- |
| WA | WA-811-RCW19.122 (verified_statute_text) | RCW 19.122.020(29),(31); 19.122.030(2),(5),(6) — https://lawfilesext.leg.wa.gov/law/RCW/RCW%20%2019%20%20TITLE/RCW%20%2019%20.122%20%20CHAPTER/RCW%20%2019%20.122%20.030.htm ; definitions/tolerance zone: https://app.leg.wa.gov/RCW/default.aspx?cite=19.122.020 | 2 to 10 full business days before work begins (030(2)) | Within 24 in of both sides of the facility (020(31)) | Marks expire 45 calendar days from notice, or at the end of excavation if sooner (030(6)) | From 2026-01-01, positive response is required from all operators before digging (030(5)) |
| AZ | AZ-811-ARS40-360 (verified_statute_text) | A.R.S. 40-360.21(4),(27); 40-360.22(B),(J),(V) — https://www.azleg.gov/ars/40/00360-22.htm ; definitions/tolerance zone: https://www.azleg.gov/ars/40/00360-21.htm | Operator marks within 2 working days of the inquiry (22(B)) | Hand-expose within 24 in of the marked facility (21(4)) | Valid 15 working days from marking; request an extension at least 2 working days before expiry (22(J)) | Interactive positive response system (22(V)); R14-2-1107 needs a human browser check (state site blocks bots) |
| CO | CO-811-CRS9-1.5 (verified_statute_text) | C.R.S. 9-1.5-102(2)(a); 9-1.5-103(3),(4)(a)(I),(4)(b),(6.5) — https://content.leg.colorado.gov/sites/default/files/images/olls/crs2024-title-09.pdf | Marked within 2 business days, not counting the notice day (103(4)(a)(I)) | Marks within 18 in horizontally of the facility exterior (103(4)(a)(I)) | Valid while visible, up to 30 calendar days after the locate due date (103(4)(b)) | Positive response is required, including no-facility responses (103(4),(6.5)) |
| MN | MN-811-216D (verified_statute_text) | Minn. Stat. 216D.04 subd. 1(a), 4(a), 4(c) — https://www.revisor.mn.gov/statutes/cite/216D/full | At least 48 h (excluding the notice day, weekends and holidays) and at most 14 calendar days before work (subd. 1(a)) | Precise location required within 2 ft of either side of the mark (subd. 4(a)) | 14 calendar days from the start time; renew at least 48 h before expiry (subd. 4(c)) | No positive-response language found in ch. 216D |
| OR | OR-811-ORS757 (**unverified_conflict**) | ORS 757.557(2); OAR 952-001-0010(23),(25), -0070(1) — https://www.oregonlegislature.gov/bills_laws/ors/ors757.html | 2 to 10 business days (ORS 757.557(2), statute text verified) | 24 in (OAR 952-001-0010(25)) | **CONFLICT:** the 2025 OAR compilation says 45 days, but OUNC announced a change to 30 days from 2026-01-01. Do not cite either until a human confirms | ACC-REG-STATE-VERIFY-2 (@data-planner) |
| ID | ID-811-IC55-22 (verified_statute_text) | Idaho Code 55-2202(21); 55-2205(1),(2); 55-2207(2)(a) — https://legislature.idaho.gov/statutesrules/idstat/Title55/T55CH22/SECT55-2205 ; definitions/tolerance zone: https://legislature.idaho.gov/statutesrules/idstat/Title55/T55CH22/SECT55-2202 | 2 to 10 business days before work; owner responds within 2 business days (55-2205) | Within 24 in horizontally (55-2202(21)); hand dig within 24 in (55-2207(2)(a)) | Up to 4 consecutive weeks from notification, unless agreed in writing (55-2205) | No explicit statutory positive-response term found |

SOW sizing rule of thumb: plan each work area for the notice period plus ticket renewals across the field-removal phase. Phase 8 can run 4 to 12 weeks. At the 12-week upper end it runs longer than the ticket life in every state above, which range from 14 days (MN) to 45 days (WA). Budget at least one renewal per area, and three or more in AZ and MN.

## 3. ROI calculator inputs (to be backed by ACC-DA-VALUE-METRICS)

| Input | Formula / source | Owner |
| --- | --- | --- |
| Copper recoverable (lbs) | sum(cable length x lbs per foot by gauge/pair count) from copper plant tables | @data-analyst |
| Salvage value ($) | copper lbs x reference price x buyer recovery % (net of lead-sheath handling) | @data-analyst |
| Opex savings ($/yr) | maintenance, trouble tickets, power for retired wire centers | @data-analyst |
| Real-estate value ($) | central offices / huts freed | partner input |
| Program cost ($) | sum of SOW phase costs above | partner input |
| Payback (months) | program cost / (monthly opex savings + salvage proceeds amortized) | @data-analyst |

**WITHDRAWN (2026-10-24):** the earlier "$43.3M net salvage / 0-month payback" headline. It used device weight x 30% copper and overstated copper about 250x. Do not reuse it anywhere.

### 3a. Slide one for a customer CFO (value case, v0.4)

> **"Copper retirement is an operating-cost and risk program. Salvage pays for removal, not for the program."**
>
> 1. **The prize is opex.** AT&T estimated its full-year 2024 direct expense for its entire legacy copper footprint at **$6B a year**: about 60% geographic costs (power, maintenance, real estate) and 40% customer costs (installation, care). Excludes capex and legacy IT. Source: AT&T 2024 Analyst & Investor Day, slide p.58 — https://investors.att.com/~/media/Files/A/ATT-IR-V2/reports-and-presentations/2024-analyst-day-with-notes.pdf
> 2. **Fiber costs less to run.** AT&T: "the cost for us to maintain a fiber subscriber is 35% less than copper subscribers" (transcript p.10) — https://investors.att.com/~/media/Files/A/ATT-IR-V2/reports-and-presentations/transcript-2024-12-03.pdf . Analysys Mason (2022, p.35, citing the Fiber Broadband Association, 2020): FTTH opex is 50% to 63% lower per home passed than HFC and DSL — https://www.analysysmason.com/contentassets/b891ca583e084468baa0b829ced38799/main-report---infra-investment-2022.pdf
> 3. **Salvage is a cost offset.** At the IMF Sep-2026 copper price (https://fred.stlouisfed.org/series/PCOPPUSDM) and NIST copper mass per foot (https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf), recovered copper nets about **$2.25 to $6.88 per lb** after removal cost (`v_roi_sensitivity`, 27 cases). It offsets removal; it does not fund the program.
> 4. **The accelerator's job** is to sequence wire centers so opex comes out early: lowest regulatory friction, highest opex per line, fiber-ready first.

All three sources were fetched (HTTP 200) and the quoted text located in the PDFs on 2026-10-24 by @pm. These are **carrier-level and industry benchmarks, not a per-line figure for the customer**. The customer's own copper O&M per line is a discovery input (`roi_calculator_assumptions.opex_saved_per_line_year` = PARTNER_DISCOVERY_INPUT). Apply the 35% to 63% reduction range to that number.

### 3b. Demo-dataset numbers (synthetic; query `v_partner_value_wire_center`, 103 wire centers, 2026-10-24)

| Metric | Value | Basis |
| --- | --- | --- |
| Copper in place / recoverable | 34.0K lb / 23.8K lb | NIST AWG pair-ft method on **synthetic** plant |
| Gross salvage | $156K | IMF PCOPPUSDM 2026-09 $6.5649/lb (real price) |
| Decommission cost | $3.98M | **Synthetic** |
| Net salvage | -$3.82M | Gross salvage minus decommission |
| Annual opex savings | $2.63M/yr | **Synthetic**; not yet tied to the 35-63% benchmark |
| Fiber build | $148.3M | **Synthetic** |
| Simple payback, ex-fiber | ~17 months | (decommission - salvage) / opex |
| 10-yr NPV at 8% (illustrative), ex-fiber | +$13.8M | -$3.82M + $2.63M x 6.71 annuity factor |
| 10-yr NPV at 8% (illustrative), incl. fiber build | -$134.4M | Fiber build must be justified by fiber revenue, which is not modelled |

How to present this: it shows the **method** on synthetic data, not a forecast. The honest story is that decommissioning copper pays back on opex in under 2 years. The fiber overbuild is a separate growth investment and is justified by fiber revenue, not by copper savings. The 8% discount rate and 10-year horizon are illustrative placeholders. Replace them with the carrier's WACC in discovery. **Partner validation:** no partner or carrier has validated this narrative yet (CEO ask D, SME reviewer).

## 4. Discovery questionnaire (draft)
* Copper footprint: number of wire centers, route miles aerial vs buried, cable gauges, records quality.
* Lead-sheathed cable: known inventory, prior sampling, environmental counsel engaged?
* Customers still on copper by segment; fiber/fixed-wireless coverage overlap.
* Regulatory: states in footprint, past copper retirement notices and Section 214 filings, state PUC commitments.
* Field: in-house vs contractor removal, 811 ticket volumes, damage history.
* Salvage: existing scrap buyers, chain-of-custody process, pricing terms.
* Data platform: Databricks workspace, Unity Catalog, source systems for plant inventory, OSS/BSS, GIS.

**Gaps the partner must close in discovery** (the accelerator cannot close these from public sources):
* Municipal ROW / street-cut permit rules and lead times for each city in wave 1 (phase 5).
* Oregon one-call ticket life (OAR 45 days vs OUNC-announced 30 days from 2026-01-01; §2a). ID is verified at 4 consecutive weeks (Idaho Code 55-2205). Confirm the WA positive-response rule (RCW 19.122.030(5)) with the carrier's locate coordinator.
* State lead-cable disposal rules and whether the RCRA scrap-metal exclusion applies to the carrier's lead-sheathed cable. Needs the carrier's environmental counsel (phase 7).
* State scrap-metal dealer licensing and record-keeping rules for each salvage buyer state (phase 9).
* State PUC copper-retirement / discontinuance notice rules on top of the federal rules (phases 3-4).
* Pole-attachment and joint-use agreement terms for aerial removal (phase 8).
* The carrier's actual salvage recovery rate, removal labor $/ft, and opex per retired wire center (§3 inputs).
* A named carrier field-ops SME to sign off the phase durations in §2.

## 5. Demo script (merged from DEMO-RUNBOOK.md §2/§6 and demo_kpi_cheat_sheet.md)

Run the demo in the **unified accelerator app** (evolved `retirement-plan`). The standalone regulatory-assistant and dig-triage apps were deleted on 2026-10-24 (asset_ledger 97, 108). Regulatory and Dig Triage are tabs in the unified app. Map/Risk still runs in the standalone `copper-map` app until ACC-APP-PORT-MAP lands (target 2026-10-25), and Commodity runs in `commodity-dashboard` until ACC-APP-PORT-COMMODITY lands (target 2026-10-26). **Pre-req:** the unified app's service principal needs UC read grants (ACC-PM-APP-SP-GRANTS, CEO action). Without them every tab shows an error state, so check this before any customer demo.

**T-10 to T-1 warm-up**
1. Warm the SQL warehouse: `SELECT COUNT(*)` on `gold_wire_center_scorecard`, `gold_device_risk_predictions`, `gold_circuit_revenue_at_risk` (all in `cdm_tmforum.copper_retirement`).
2. Warm serving endpoint `copper-retirement-risk` (scale-to-zero, 60-90 s cold start). Send one request with all 39 V5 features; the feature contract is in the model card (ACC-ML-MODEL-CARD).
3. Open the Map tab: H3 hexagons coloured by risk; click a hexagon to see device count, risk score and customer count; filter by state and risk tier.
4. Open the unified app **Regulatory** tab (`#regulatory`) and ask "What notice must an ILEC give before retiring copper?". Expected answer: 90 days direct notice (15 if no customers), citing FCC 26-19 / 47 CFR 51.333 with the official URL (see §2 phase 3). Never demo an answer without a citation.
5. Final check: warehouse RUNNING, endpoint READY, Map and Regulatory tabs rendering live data (not error states), and the Regulatory answer shows [S#] official-URL chips.

**Beat 1 — "Where is our copper and what is the risk of touching it?"** Map US view, zoom to a region, click a hexagon, filter to critical.
**Beat 4 — "Are we clear on regulations everywhere we touch?"** Ask the federal question, then a footprint-state 811 question (WA/AZ/CO/MN/OR/ID), and show the citations. **Gate:** Beat 4 can run live from the unified app Regulatory tab, which uses real chunks only and shows citations. Present only answers that show [S#] official-URL chips, and do not present matrix rows that are not verified (§2 phase 2). Full sign-off waits for ACC-QA-REG-CITATIONS. Fallback: show the cited 811 table in §2a.

**Presenter KPIs (synthetic demo data, snapshot 2026-09-19; refresh from the metric views before each demo):**

| KPI | Value | Metric view |
| --- | --- | --- |
| Copper devices / wire centers | 2,672 / 103 | `copper_retirement_project_status` |
| Critical-risk devices | 383 (14.3%) | `copper_retirement_project_status` |
| Fiber-ready devices | 122 (4.6%) | `copper_retirement_project_status` |
| Customers / services impacted | 288 / 304 | `copper_customers_impacted` |
| Critical-impact customers | 64 | `copper_customers_impacted` |
| Annual revenue at risk | $603.8M across 14,777 circuits | `copper_ebitda_impact_achieved` |
| High-value circuits | 1,777 ($327.8M) | `copper_ebitda_impact_achieved` |
| Revenue tied to PUC filings | $53.9M | `copper_ebitda_impact_achieved` |
| Base-scenario EBITDA impact | $32.2M over 6 quarters, peak 2027-Q2 $9.2M | `copper_ebitda_impact_forecast` |
| Net salvage (demo, synthetic) | -$3.82M; opex-led payback ~17 months ex-fiber (see §3b) | `copper_partner_value` / `v_partner_value_wire_center` |

## 6. Deploy and environment baseline (merged from DEMO-ENV-FREEZE-CHECKLIST.md; README.md kept)

One command (host comes from the partner's CLI profile; nothing workspace-specific is hard-coded in `databricks.yml`):

`databricks bundle deploy -t partner --var warehouse_id=<WAREHOUSE_ID> --var catalog_name=<CATALOG> [--var schema_name=... --var vs_endpoint=... --var vs_index=... --var serving_endpoint=... --var lakebase_project=... --var lakebase_branch=...]`

Run `databricks bundle validate -t partner --var warehouse_id=<WAREHOUSE_ID>` first. `BUNDLE_VAR_<name>` environment variables work instead of `--var`. Targets: `partner` = fresh workspace (also creates the schema); `dev` / `staging` / `prod` = reuse existing catalog + schema. The bundle deploys 1 pipeline, 1 daily refresh job, and 2 apps (unified accelerator + copper-task-board). Validated 2026-10-24 on all 4 targets (@devops).

**Prerequisites the bundle does not create:** the UC catalog (with TMF SID source schemas that the pipeline reads), a SQL warehouse, a Lakebase project, a Vector Search endpoint + index, and the risk serving endpoint (created by the retrain template in `beat1_risk_model_walkthrough`). The Lakebase sync job is disabled until `scripts/sync_gold_to_lakebase.py` lands (ACC-CREATE-LAKEBASE-SYNC-SCRIPT).

| Component | Reference implementation (this workspace) | Partner variable |
| --- | --- | --- |
| Catalog / schema | `cdm_tmforum.copper_retirement` | `catalog_name`, `schema_name` |
| Pipeline | `copper-retirement-pipeline` (b52532a2-6398-44ed-b239-9e95cafb745c), serverless, 8 MVs: bronze_copper_devices, bronze_copper_services, bronze_dig_safe_incidents, silver_copper_plant_enriched, silver_device_service_impact, gold_wire_center_scorecard, gold_contractor_scorecard, gold_retirement_executive_summary | — |
| Risk model | `cdm_tmforum.ml_models.copper_retirement_risk` V5 champion (LightGBM, 39 features, AUC 0.986), V4 fallback | — (set in retrain notebook) |
| Serving endpoint | `copper-retirement-risk`, Small, scale-to-zero, inference logging to `risk_model_inference_payload` | `serving_endpoint` |
| Vector Search | endpoint `cmeg-demos-vs` (per DEC-VS-ENDPOINT-ACTUAL); index `regulatory_doc_chunks_vs_index` on `regulatory_doc_chunks`, `databricks-bge-large-en` (1024-dim), HYBRID, TRIGGERED sync. A duplicate `regulatory_doc_vs_index` sits on `demo_telco_vs_endpoint` and is not used | `vs_endpoint`, `vs_index` |
| Lakebase | project `copper-task-board`, branch `production`, schema `copper_app` (app data) | `lakebase_project`, `lakebase_branch` |
| SQL warehouse | Serverless Starter Warehouse 7b65956f30d66feb (backup telco-builders da0dbcd5676d37eb) | `warehouse_id` |
| Apps (R2 target) | unified accelerator app (evolved `retirement-plan`) + internal `copper-task-board` | — (names suffixed `-<target>`) |

Baseline row counts after a clean build (V1 snapshot, synthetic): bronze_copper_devices 2,672; bronze_copper_services 17,655; silver_copper_plant_enriched 2,672; silver_device_service_impact 440; gold_wire_center_scorecard 103; gold_circuit_revenue_at_risk 14,777; gold_contractor_scorecard 10,000; gold_retirement_executive_summary 6; gold_device_risk_predictions 2,672. Lakebase copper_app: device_risk_map 2,672; wire_center_scorecard 103; wire_center_boundaries 1,699; contractor_scorecard 10,000; retirement_plan 200; retirement_milestones 927; dig_incidents 5,000; jurisdiction_requirements 56; commodity_prices 10,482. `regulatory_doc_chunks` now holds 1,598 real chunks plus 528 synthetic chunks (2026-10-25). The synthetic chunks and `copper_app.regulatory_documents` (297, synthetic) are retired under ACC-REG-SYNTHETIC-RETIRE, so these counts will change.

### 6a. Fresh-workspace dependency inventory (static desk check, @pm 2026-10-25)

This comes from reading the 4 active bundle resources, `pipeline/*.sql` (11 files) and `apps/retirement-plan` source. It is not a live deploy. Until ACC-QA-FRESH-DEPLOY passes, treat a clean `partner` deploy as **not yet proven**.

| # | Dependency | Read by | In bundle? | Gap / owner |
| --- | --- | --- | --- | --- |
| 1 | TMF SID source schemas `tmf_enterprise` (physical_device, work, project, milestone, budget, workforce_*), `tmf_resource.device_service_allocation`, `tmf_service.customer_facing_service` | pipeline bronze/silver, Plan tab queries | No | A fresh catalog has none of these tables, so the pipeline fails at bronze. The seed job is ACC-DE-SEED-JOB, which reuses `scripts/generate_synthetic_sources.py`. |
| 2 | `oracle_erp_source.*` (ra_billed_circuit_rates, ra_customer_trx_all, revenue_recognition_schedule), `ironclad_clm_source.contract_record` | silver_revenue_recognition_constraints, silver_contract_constraints, gold_circuit_revenue_at_risk | No | Same as #1 (ACC-DE-SEED-JOB). |
| 3 | `copper_plant_wire_center_jurisdiction`, `dig_safe_incident`, `contractor_performance` in `${schema_name}` | silver_copper_plant_enriched, bronze_dig_safe_incidents, gold_contractor_scorecard | No | Same as #1. The 6 legacy footprint states only (DEC-DSI-FOOTPRINT). |
| 4 | `provable_resilience_intelligence.stg_811_dig_ticket` | Dig Triage tab | No | This comes from another project's schema. The partner either supplies 811 data or seeds a synthetic table. ACC-DE-SEED-JOB must cover it, or the tab must degrade gracefully. |
| 5 | Regulatory corpus: volume `regulatory_source_docs`, `regulatory_source_register`, `regulatory_doc_chunks`, TVF `search_regulatory_chunks`, `jurisdiction_requirements_cited` | Regulatory tab | No | The ingest/parse code exists but is not a bundle job. Follow-up after ACC-DE-SEED-JOB. |
| 6 | Hard-coded `cdm_tmforum.*` in app SQL (server/databricksSQL.js, routes/triage.js, tabs/triage/lib/triageApi.ts, config/queries/*.sql) | unified app | — | The app ignores `--var catalog_name`. Fix in ACC-QA-DEF-APP-CATALOG (@app-developer). |
| 7 | Warehouse id `9cd919d96b11bf1c` hard-coded in `apps/retirement-plan/app.yaml` | unified app | Partly: the bundle attaches `sql-warehouse` from `${var.warehouse_id}` | app.yaml should read the `sql-warehouse` resource with `valueFrom`. Fix in ACC-DEVOPS-RM-REGASSIST-BUNDLE (@devops). |
| 8 | Serving endpoints `copper-retirement-risk` and LLM `databricks-claude-sonnet-4-5` | Map/Risk, Regulatory tabs | No (prerequisite) | The partner runs the retrain template (`beat1_risk_model_walkthrough`). The LLM must exist as a pay-per-token endpoint in the partner region. |
| 9 | Vector Search endpoint + index | Regulatory tab (target design) | No (prerequisite) | Interim retrieval uses the Delta TVF (#5), so VS is optional until ACC-REG-VS-RESYNC. |
| 10 | App service-principal UC grants (USE CATALOG/SCHEMA, SELECT, EXECUTE) | all tabs | No | Granted by hand today and still missing in the reference workspace (ACC-PM-APP-SP-GRANTS). The bundle should declare grants on the `partner` schema resource. |
| 11 | Lakebase project + `copper_app` schema DDL | copper-task-board, app write-back | No (prerequisite) | DDL script not packaged. The sync job is disabled (ACC-CREATE-LAKEBASE-SYNC-SCRIPT). |

Shortest path to a provable one-command partner deploy: ACC-DE-SEED-JOB (#1-4), then ACC-QA-DEF-APP-CATALOG (#6), then ACC-DEVOPS-RM-REGASSIST-BUNDLE (#7), then ACC-QA-FRESH-DEPLOY.

Demo freeze rule: in the 48 h before a customer demo, do not change the model version, re-index VS, edit pipeline SQL or redeploy apps.

## 7. Recovery (merged from DEMO-ROLLBACK-RECOVERY.md)

| Symptom | Fix | Time |
| --- | --- | --- |
| App 502 / blank | `w.apps.stop(name)`, wait 10 s, `w.apps.start(name)`; if that fails, redeploy from source with `w.apps.deploy(name, source_code_path=..., mode="SNAPSHOT")` | 1-2 min |
| Risk colours missing / endpoint NOT_READY | Send a warm-up request (scale-to-zero) | 60-90 s |
| Endpoint FAILED | Recreate `copper-retirement-risk` with V5, Small, scale-to-zero, auto-capture to `copper_retirement.risk_model_inference*` | 5-10 min |
| Predictions look wrong | `update_config` served entity to V4 | 3-5 min |
| Regulatory search empty | Check the index with `get_index`; `sync_index` on the VS index; confirm the source table row count; if the VS endpoint is offline, escalate to a workspace admin | 5-15 min |
| Gold tables empty or stale | `w.pipelines.start_update(pipeline_id, full_refresh=True)`, then re-check §6 counts. Do not drop managed tables | 5-10 min |
| Pipeline SQL corrupted | `git checkout v1.0-demo -- pipeline/`, then refresh | 5-10 min |
| Warehouse down | `w.warehouses.start(id)`; else point app `DATABRICKS_WAREHOUSE_ID` at the backup and redeploy | 1-3 min |
| Lakebase refused / expired token | Regenerate with `w.postgres.generate_database_credential(endpoint=...)`; a suspended project resumes on the first query | 30-60 s |
| Whole repo in unknown state | `git stash && git checkout v1.0-demo` (restores code only, not UC data, endpoints, VS or Lakebase), then rerun the pipeline | 15-30 min |

## 8. Run cost (measured; for the partner's TCO slide)

Measured in this workspace from `system.billing.usage` joined to `system.billing.list_prices` (list $, AWS us-east-1, Enterprise) for 2026-10-17 to 2026-10-24:

| Component | 7-day list $ | Ships to partner? |
| --- | --- | --- |
| 6 Databricks Apps, always on (86 DBU each, $81.70 each) | $490.20 | 2 apps in R2. **Note (2026-10-25):** this 7-day window is historical. 4 apps are ACTIVE now (retirement-plan, copper-map, commodity-dashboard, copper-task-board) after dig-triage and regulatory-assistant were deleted, for a current run-rate of about $326.80/week. |
| Vector Search endpoint `cmeg-demos-vs` (hosts the live regulatory index; 672 DBU, 2026-10-17..23) | $47.04 | Yes (1 endpoint) |
| Vector Search endpoint `demo_telco_vs_endpoint` (shared by 7 indexes, incl. the unused duplicate) | $48.16 | No |
| Lakebase `copper-task-board` | $13.05 | copper_app schema only |
| Serving `copper-retirement-risk` (scale-to-zero) | $0.16 | Yes |
| Agent swarm serverless notebook compute (69 copper runs) | $18.15 | No (build-time only) |
| Agent swarm Genie Code usage (estimated pro-rata 69/1,490 conversations of $4,953.93) | ~$229 | No (build-time only) |
| **Total** | **~$846 / week** | |

Retiring commodity-dashboard, copper-map, dig-triage and regulatory-assistant saves $326.80/week (about $46.69/day, about $1,400/month).

**Estimated partner steady-state run cost:** about $1,000/month list. That is 2 apps at about $350/month each, plus VS endpoint about $206/month, Lakebase about $56/month and serving close to $0 idle. SQL warehouse and pipeline refresh costs come on top and depend on usage. Re-measure on the partner's cloud/region.
