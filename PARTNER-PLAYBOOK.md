# Copper Retirement Solution Accelerator — Partner Playbook (DRAFT v1.2)

> Owner: @pm. Task: ACC-DOCS-PARTNER-PLAYBOOK. Status: DRAFT v1.2 (2026-10-25 23:05 UTC). v1.2 fixes the stale counts that @qa found (ACC-QA-DEF-PLAYBOOK-V11-STALE). The matrix is now 68 rows: 49 VERIFIED_STATUTE_TEXT, 16 VERIFIED_OFFICIAL_PAGE, 1 DERIVED_FROM_STATUTE, 1 UNVERIFIED and 1 STATE_GAP. §2c lists the five cited state lead rules, and only AZ is still STATE_GAP. The AZ notice lead time is labeled DERIVED. The CO notice lead time is labeled as the operator marking window. The AZ emergency cell is resolved (A.R.S. 40-360.28(F)(1)). v1.2 also adds §2e, a field line-item pricing table that answers COO-Q-20261025-1750-5: field work is NOT priced yet. It refreshes §3a and §3b for ACC-DA-FIXFILING (one-time cost $4.82M, payback 163.2 months on the metric view vs 25.7 months on the sensitivity base, which are not reconciled). Earlier: v1.1 (2026-10-25 17:10 UTC) fixes two stale Oregon labels: the §2 phase 6 row and the §2a OR row no longer say `unverified_conflict`, because the OR ticket life is verified from the OUNC 2026 Addendum. It also adds §2d, a one-table check of the SOW inputs against the matrix (answers COO-Q-20261025-0549-4). Earlier: v1.0 (2026-10-25 12:10 UTC) restates the jurisdiction counts after ACC-DA-JUR-REMERGE (68 rows, 61 verified; Oregon 811 rows now verified), updates the corpus to 1,719 real chunks from 45 official URLs, removes the unsourced synthetic $55K-per-wire-center regulatory filing cost from the value case (decision DEC-ROI-FILING-COST: it is a partner discovery input), records the regulatory RAG eval passing the 80% gate, and flags the AZ emergency-excavation cell as under review (ACC-QA-DEF-AZ-EMERG-ROW). Earlier: v0.9 (2026-10-25 11:10 UTC) updates §5 and §5a for the @app-developer r2 code changes (not yet deployed): the Plan tab now reads Unity Catalog only, and its regulatory checklist is built from the cited jurisdiction matrix. Dig Triage now shows true error states instead of 'not found'. It also fixes a stale Oregon line in §4. Earlier: v0.8 (2026-10-25 09:10 UTC) binds the §2 SOW field phases to the real per-state rules (COO-Q-20261025-0549-4). §2a now resolves the Oregon ticket life (30 days, effective 2026-01-08). New §2b covers white-lining, emergency and positive-response rules per state, plus ticket counts per 12-week wave. New §2c states the lead-sheath handling rules and the state gap. Earlier: v0.7 (2026-10-25 06:10 UTC) rewrites §3b on the rescaled opex (ACC-DA-OPEX-RESCALE): the ~17-month payback and the +$13.8M NPV are withdrawn, and no demo-dataset payback or NPV is a sales number. It adds the §3a transferable claim and discovery inputs (COO-Q-20261024-1800-2), the dated §5a demo fallback and legacy-app deletion gate (COO-Q-20261025-0549-3), and the @qa ACC-QA-DEF-PB-V06 count fixes. Earlier: v0.6 (2026-10-25 05:10 UTC) added §6a, a static fresh-workspace dependency inventory: what a clean `bundle deploy -t partner` needs before the pipeline and app can run. It is a desk check, not a live fresh deploy (that is COO-Q-20261024-1800-3 / ACC-QA-FRESH-DEPLOY). Earlier: v0.5 (2026-10-25 00:30 UTC). v0.5 applies the @qa ACC-QA-DEF-PB-V04 fixes: the jurisdiction matrix is live, the Regulatory tab answers are citable through interim Delta retrieval, the §5 demo script now uses the unified app, the app count is current, and the corpus is 1,598 real chunks. v0.4 restated the §3 value case: the $43.3M salvage headline is withdrawn and replaced by an opex-led, cited value case (COO-Q-20261024-1800-2, ACC-PM-PLAYBOOK-ROI-RESTATE). It also applies the @qa ACC-QA-DEF-PB-V03 fixes (VS endpoint/model, §8 cost, stale 811 text, ID ticket life, subsection URLs). v0.3 rebuilt the §2a 811 table from verified statute text. Sections 5-7 now absorb DEMO-RUNBOOK.md, DEMO-ROLLBACK-RECOVERY.md, DEMO-ENV-FREEZE-CHECKLIST.md and demo_kpi_cheat_sheet.md (content merged 2026-10-24; the 4 source files are **not yet deleted**. Workspace deletion by a scheduled agent was blocked, so it is pending CEO approval. Originals are also in git history on origin/main of github.com/skhage/copper-retirement, commits a6aa6d0 and 946b559). README.md is kept as the repo root readme and now points here.
>
> Rule for this document: every regulatory statement carries an official URL. Anything not yet verified is marked **GAP** and is not to be presented to a customer as fact. Durations are planning assumptions for SOW sizing, not regulatory requirements, and must be validated by the partner's field-operations lead.

## 0. Data disclosure
The demo dataset (Lakelink Fiber) is **synthetic**. Device, customer, wire-center, contractor and dig-incident data are generated. Regulatory content is being replaced with real downloaded sources (R1). Status as of 2026-10-25: `regulatory_doc_chunks` holds **1,719 real chunks from 45 distinct official URLs** (0 rows without a `source_url`; counted 2026-10-25 12:05 UTC), plus 528 legacy chunks flagged `is_synthetic = true`. The unified app's **Regulatory tab answers only from the real chunks** (`is_synthetic = false`). Each answer carries [S#] chips that link to the official URL, and the tab replies "No official source found" when nothing matches. @qa found 20 of 20 sampled answers cited real URLs. On 2026-10-25 the regulatory RAG eval passed its 80% gate on 3 consecutive runs (33/38, 31/38, 32/38) with 100% URL validity against the source register, 100% jurisdiction correctness and 100% gap abstention (@ml-engineer, ACC-ML-REG-PROMPT-TUNE). Retrieval currently runs through the interim Delta function `cdm_tmforum.copper_retirement.search_regulatory_chunks(query, k)` (bge-large cosine search, returns `source_url` on every row). The VS index `regulatory_doc_chunks_vs_index` still serves the 528 synthetic chunks until the same-name recreate (ACC-VS-INDEX-RECREATE, CEO action) and re-sync (ACC-REG-VS-RESYNC). Until then, do not point any client at the VS index directly. Copper price is now a real public series: IMF Primary Commodity Prices, copper (PCOPPUSDM, monthly, USD/metric ton) in `cdm_tmforum.copper_retirement.copper_commodity_price_official` (417 rows; `source_url` = https://fred.stlouisfed.org/series/PCOPPUSDM). LME (https://www.lme.com/en/metals/non-ferrous/lme-copper) is licensed and kept as a reference only. Copper volumes, plant, customers and costs remain **synthetic**.

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
| 2 | Wave planning | 2-3 weeks | Partner PM, carrier engineering + regulatory affairs | Retirement waves, customer migration plan, jurisdiction requirements matrix per wave | Jurisdiction matrix: `cdm_tmforum.copper_retirement.jurisdiction_requirements_cited` (68 rows; 65 verified: 49 `VERIFIED_STATUTE_TEXT` and 16 `VERIFIED_OFFICIAL_PAGE`, counted 2026-10-25 23:05 UTC after ACC-DA-LEAD-MERGE). Every row has a section-level `citation_url` (the page that contains the cited value; it falls back to `official_url`). The matrix is shown in the unified app Regulatory tab. **GAP** for the other 3 rows: 1 `STATE_GAP` (AZ lead-sheathed cable handling, see §2c), 1 `UNVERIFIED` (AZ state discontinuance notice, R14-2-1107; the state site blocks automated download, human download requested) and 1 `DERIVED_FROM_STATUTE` (AZ 811 notice lead time, derived from the 2-working-day operator response window in A.R.S. 40-360.22(B)). Do not present those rows as fact. The CO lead row's citation is being corrected (ACC-QA-DEF-CO-LEAD-URL) |
| 3 | Regulatory notices and filings | Driven by notice periods (see source) | Carrier regulatory affairs, counsel | Copper retirement direct notices, Section 214 discontinuance application where service is discontinued, state filings | Direct notice of planned copper retirement at least 90 days before implementation (15 days if the copper serves no customers): FCC 26-19 (adopted 2026-03-26, published 91 FR 20913, 2026-04-20), Appendix A, revised 47 CFR 51.333(a)(2) — https://docs.fcc.gov/public/attachments/FCC-26-19A1.pdf . FCC 26-19 eliminates the FCC filing and Bureau public-notice/objection process for copper retirements; the ILEC still posts public notice and gives direct notice. Section 214 discontinuance: 47 CFR 63.71 — https://www.ecfr.gov/current/title-47/section-63.71 ; FCC 26-19 applies a 31-day automatic grant period to all discontinuance applications (Section III.B). **Effectiveness:** the order said these amendments (51.329, 51.333, 63.60, 63.62, 63.63, 63.71, 63.602) would not take effect until OMB PRA review (para 120). WCB announced OMB approval (control nos. 3060-0149, 3060-0741) and the amendments are **effective 2026-10-15**: 91 FR 62334, FR Doc. 2026-20192, published 2026-10-01 — https://www.federalregister.gov/documents/2026/10/01/2026-20192/wc-docket-nos-25-208-25-209-fcc-26-19-fr-id-370342-reducing-barriers-to-network-improvements-and (verified via federalregister.gov API, `effective_on` = 2026-10-15, on 2026-10-24). Notices served before 2026-10-15 fall under the prior rules (FCC 17-154 https://docs.fcc.gov/public/attachments/FCC-17-154A1_Rcd.pdf , FCC 18-74 https://docs.fcc.gov/public/attachments/FCC-18-74A1_Rcd.pdf ). **GAP:** eCFR may lag the amendment, so check the current eCFR text before quoting rule wording; state notice requirements per state |
| 4 | Customer migration | Parallel to phase 3, 6-12 weeks | Carrier care/sales, field install | Customers migrated to fiber/alternative service, migration KPI tracking | Customer notice obligations tied to discontinuance — see 47 CFR 63.71 above; state consumer rules **GAP** |
| 5 | Permits and right-of-way | 2-8 weeks, jurisdiction dependent | Partner permitting coordinator, carrier outside-plant | ROW / municipal permits, traffic control plans | Utilities on federal-aid highway ROW: 23 CFR Part 645 — https://www.ecfr.gov/current/title-23/chapter-I/subchapter-G/part-645 . Municipal permit rules **GAP** (local) |
| 6 | 811 locates and dig safety (buried plant) | Wait period set by state one-call law, plus ticket renewals per wave | Excavation contractor, carrier locate coordinator | One-call tickets per work area, positive response confirmation, dig-triage risk scoring (Dig Triage tab) | Locate underground installations before excavation: OSHA 29 CFR 1926.651(b) — https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.651 . Use one-call and wait for marks before excavating near pipelines: PHMSA 49 CFR Part 196 — https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-D/part-196 ; state damage-prevention programs: 49 CFR Part 198 — https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-D/part-198 . Industry practice: CGA Best Practices v21 — https://bestpractices.commongroundalliance.com/Portals/1/Best%20Practices%20Guide%20Version%2021%20PDF%20Download.pdf . Excavation protection: OSHA 29 CFR 1926 Subpart P (1926.651 above). Per-state notice, tolerance and ticket life: see §2a (sourced from `regulatory_source_register`; WA, AZ, CO, MN and ID are `verified_statute_text`; OR notice is statute text, and the OR ticket life is verified from the OUNC 2026 Addendum, register OR-811-OUNC-2026-ADDENDUM) |
| 7 | Lead-sheathed cable assessment and handling | 1-3 weeks per wave (sampling, plan) | Environmental consultant, safety officer, removal contractor | Lead-sheath inventory flag per span, worker exposure plan, handling and disposal plan | Worker lead exposure in construction: OSHA 29 CFR 1926.62 — https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.62 . EPA has run response actions on lead telecom cable (Louisiana Lead Cable site) — https://response.epa.gov/site/site_profile.aspx?site_id=16204 . Scrap metal recycling exclusions under RCRA: 40 CFR 261.4 and 261.6 — https://www.ecfr.gov/current/title-40/chapter-I/subchapter-I/part-261/section-261.4 , https://www.ecfr.gov/current/title-40/chapter-I/subchapter-I/part-261/section-261.6 . State rules: see §2c. **GAP:** whether the scrap-metal exclusion applies to lead-sheathed cable must be confirmed by environmental counsel. Not priced yet, see §2e |
| 8 | Field removal — aerial vs buried | 4-12 weeks per wave | Removal contractor, carrier outside-plant inspector | Spans removed, pole attachments cleared, restoration sign-off | Telecom worker safety (incl. aerial work): OSHA 29 CFR 1910.268 — https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.268 . Pole-attachment / joint-use agreements **GAP** (contractual) |
| 9 | Salvage, chain of custody and sale | 2-6 weeks per wave | Salvage buyer, carrier asset recovery, finance | Weighed lots, chain-of-custody records, buyer settlement vs reference price, recovery report | Reference price: LME copper (https://www.lme.com/en/metals/non-ferrous/lme-copper, licensed data). State scrap-metal dealer and record-keeping laws **GAP** |
| 10 | Decommission and close-out | 2-4 weeks | Partner PM, carrier finance | Inventory/records retired, opex and real-estate savings booked, value report from partner value metric view | None (internal) |

Validation status: drafted by @pm from official sources above on 2026-10-24. **Not yet validated by a carrier or partner field-operations SME.** CEO was asked to name a reviewer on 2026-10-24 (status_updates id 113); no reviewer named as of 2026-10-24 09:00 UTC. Re-asked in today's rollup.

### 2a. 811 one-call requirements — footprint states (planning use only)

Source: `cdm_tmforum.copper_retirement.jurisdiction_requirements_cited` (68 rows; `requirement_type LIKE '811_%'`) and `regulatory_source_register` (50 rows, 49 verified; last 10 added by @data-planner ACC-DP-JUR-NOTFOUND on 2026-10-25). @qa ACC-QA-REG-CITATIONS passed on 2026-10-25: 29 of 30 matrix URLs return HTTP 200 with the rule text, and 33 of 34 numeric values were found verbatim. v0.8: the Oregon ticket-life conflict is resolved from the register (see the OR row). v1.0: ACC-DA-JUR-REMERGE ran on 2026-10-25 11:27 UTC, and all six Oregon 811 cells in the matrix are now verified (notice lead time from statute text; the other five from the OUNC official pages). Still for planning use only, because no field-operations SME has reviewed it. v0.3 corrections: AZ hand-dig zone is 24 in, not 18 in. The MN "6 months with refresh" claim is removed because it was not verified.

| State | register source_id | Statute (official URL) | Notice before digging | Tolerance zone | Ticket / mark life | Open item |
| --- | --- | --- | --- | --- | --- | --- |
| WA | WA-811-RCW19.122 (verified_statute_text) | RCW 19.122.020(29),(31); 19.122.030(2),(5),(6) — https://lawfilesext.leg.wa.gov/law/RCW/RCW%20%2019%20%20TITLE/RCW%20%2019%20.122%20%20CHAPTER/RCW%20%2019%20.122%20.030.htm ; definitions/tolerance zone: https://app.leg.wa.gov/RCW/default.aspx?cite=19.122.020 | 2 to 10 full business days before work begins (030(2)) | Within 24 in of both sides of the facility (020(31)) | Marks expire 45 calendar days from notice, or at the end of excavation if sooner (030(6)) | From 2026-01-01, positive response is required from all operators before digging (030(5)) |
| AZ | AZ-811-ARS40-360 (verified_statute_text) | A.R.S. 40-360.21(4),(27); 40-360.22(B),(J),(V) — https://www.azleg.gov/ars/40/00360-22.htm ; definitions/tolerance zone: https://www.azleg.gov/ars/40/00360-21.htm | Operator marks within 2 working days of the inquiry (22(B)) | Hand-expose within 24 in of the marked facility (21(4)) | Valid 15 working days from marking; request an extension at least 2 working days before expiry (22(J)) | Interactive positive response system (22(V)); R14-2-1107 needs a human browser check (state site blocks bots) |
| CO | CO-811-CRS9-1.5 (verified_statute_text) | C.R.S. 9-1.5-102(2)(a); 9-1.5-103(3),(4)(a)(I),(4)(b),(6.5) — https://content.leg.colorado.gov/sites/default/files/images/olls/crs2024-title-09.pdf | Marked within 2 business days, not counting the notice day (103(4)(a)(I)) | Marks within 18 in horizontally of the facility exterior (103(4)(a)(I)) | Valid while visible, up to 30 calendar days after the locate due date (103(4)(b)) | Positive response is required, including no-facility responses (103(4),(6.5)) |
| MN | MN-811-216D (verified_statute_text) | Minn. Stat. 216D.04 subd. 1(a), 4(a), 4(c) — https://www.revisor.mn.gov/statutes/cite/216D/full | At least 48 h (excluding the notice day, weekends and holidays) and at most 14 calendar days before work (subd. 1(a)) | Precise location required within 2 ft of either side of the mark (subd. 4(a)) | 14 calendar days from the start time; renew at least 48 h before expiry (subd. 4(c)) | No positive-response language found in ch. 216D |
| OR | OR-811-ORS757 (statute text for notice); OR-811-OUNC-2026-ADDENDUM (verified, ticket life) | ORS 757.557(2); OAR 952-001-0010(23),(25), -0070(1) — https://www.oregonlegislature.gov/bills_laws/ors/ors757.html | 2 to 10 business days (ORS 757.557(2), statute text verified) | 24 in (OAR 952-001-0010(25)) | 30 days. OAR 952-001-0010(23) changed ticket life from 45 to 30 days, effective 2026-01-08, per the OUNC 2026 Addendum to the Oregon Standards Manual: https://digsafelyoregon.com/wp-content/uploads/2026/03/2026-Addendum-to-the-Oregon-Standards-Manual_Final.pdf (register OR-811-OUNC-2026-ADDENDUM, verified). | The matrix cell is verified (VERIFIED_OFFICIAL_PAGE) as of 2026-10-25. The underlying OAR text on secure.sos.state.or.us is bot-blocked, so this rests on the issuing agency's addendum |
| ID | ID-811-IC55-22 (verified_statute_text) | Idaho Code 55-2202(21); 55-2205(1),(2); 55-2207(2)(a) — https://legislature.idaho.gov/statutesrules/idstat/Title55/T55CH22/SECT55-2205 ; definitions/tolerance zone: https://legislature.idaho.gov/statutesrules/idstat/Title55/T55CH22/SECT55-2202 | 2 to 10 business days before work; owner responds within 2 business days (55-2205) | Within 24 in horizontally (55-2202(21)); hand dig within 24 in (55-2207(2)(a)) | Up to 4 consecutive weeks from notification, unless agreed in writing (55-2205) | No explicit statutory positive-response term found |

SOW sizing rule of thumb: plan each work area for the notice period plus ticket renewals across the field-removal phase. Phase 8 can run 4 to 12 weeks. At the 12-week upper end it runs longer than the ticket life in every state above, which ranges from 14 days (MN) to 45 days (WA). The ticket counts in §2b are the basis for the locate-coordination line in the SOW.

### 2b. Field-execution rules that change SOW effort (per state; v0.8)

Planning arithmetic. For a 12-week (84 calendar day) field wave on one work area, the number of tickets is ceil(84 / ticket life). AZ working days are converted at 5 per 7 calendar days, before holidays. These are not statutory numbers. They are the partner's budget lines for locate coordination and re-marks.

| State | Pre-mark (white-lining) | Emergency excavation | Positive response | Tickets per 12-week wave (renewals) | Source (official URL) |
| --- | --- | --- | --- | --- | --- |
| WA | Required: mark the excavation boundary in white (or white pin flags) before notice, RCW 19.122.030(1)(a) | Exempt from white-lining and notice. Notify the one-number service at the earliest practicable opportunity, RCW 19.122.031(1)(a) | Required from 2026-01-01, RCW 19.122.030(5) | 2 (1) at 45 days | https://app.leg.wa.gov/RCW/default.aspx?cite=19.122.030 ; https://app.leg.wa.gov/RCW/default.aspx?cite=19.122.031 |
| AZ | Required: white-line the requested area before the location request, A.R.S. 40-360.22(C) | The civil-penalty and liability section does not apply to an emergency excavation that involves immediate danger to life, health or property, if reasonable precautions protect the facilities, A.R.S. 40-360.28(F)(1). This was resolved by ACC-QA-DEF-AZ-EMERG-ROW on 2026-10-25. Art. 6.3 sets no separate emergency-ticket procedure, and Arizona 811 emergency-ticket procedures are a **GAP**. A damage or release requires notice to 911 or the local emergency response agency, 40-360.24 | Interactive positive response system, 40-360.22(B),(V) | 4 (3) at 15 working days | https://www.azleg.gov/ars/40/00360-22.htm ; https://www.azleg.gov/ars/40/00360-24.htm ; https://www.azleg.gov/ars/40/00360-28.htm |
| CO | Conditional: only when the area cannot be described on the request. Options are white marks, electronic delineation or an on-site meet, C.R.S. 9-1.5-103(3)(c)(II) | Provision in 9-1.5-103(5) | Required, including no-facility responses, 9-1.5-103(4),(6.5) | 3 (2) at 30 days | https://content.leg.colorado.gov/sites/default/files/images/olls/crs2024-title-09.pdf |
| MN | Required: white marks (black in wintry conditions) or electronic marking, Minn. Stat. 216D.05(a)(2) | 216D.04 subd. 1(a) | Not required by statute. Operators must notify if marking will not be complete by the start time, 216D.04 subd. 3(e) | 6 (5) at 14 days | https://www.revisor.mn.gov/statutes/cite/216D/full |
| OR | Required: mark the area in white, OAR 952-001-0040 (per OUNC) | Defined in OAR 952-001-0010(7) and handled under 952-001-0060 (per OUNC) | Not required by Oregon law; CGA best practice (OUNC) | 3 (2) at 30 days | https://digsafelyoregon.com/dig-safely/faq-2/ ; https://digsafelyoregon.com/resources/positive-response/ |
| ID | Required: pre-mark the path in white, with exceptions, Idaho Code 55-2205(1)(b) | Exempt from notice time requirements, 55-2205(4)(a)-(c) | Not required by statute. The owner must respond within 2 business days, 55-2205(2) | 3 (2) at 4 weeks | https://legislature.idaho.gov/statutesrules/idstat/Title55/T55CH22/SECT55-2205 |

What this changes in the SOW:
* MN and AZ need the most locate coordination: 6 and 4 tickets per area per wave. Price the locate-coordinator role per ticket, not as a flat fee.
* WA, CO and AZ have a positive-response gate. Field crews cannot start until every operator has responded, so the Dig Triage tab's ticket status is a hard gate in those states.
* White-lining is a crew task in five of the six states. It is conditional in CO. Add it to the Phase 6 crew checklist.
* The matrix cells for the WA, CO, MN, OR and ID white-lining and emergency rows were moved to VERIFIED by ACC-DA-JUR-REMERGE on 2026-10-25. The AZ emergency cell was resolved on 2026-10-25: it now cites A.R.S. 40-360.28(F)(1) (ACC-QA-DEF-AZ-EMERG-ROW).

### 2c. Lead-sheathed cable handling (per state; v0.8)

* Federal baseline (VERIFIED): worker exposure is governed by OSHA 29 CFR 1926.62 (https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.62). The hazardous-waste toxicity threshold for lead is 5.0 mg/L TCLP, waste code D008, under 40 CFR 261.24 (https://www.ecfr.gov/current/title-40/chapter-I/subchapter-I/part-261/subpart-C/section-261.24).
* State rules (v1.2, from `jurisdiction_requirements_cited` with `requirement_type = 'lead_cable_handling'`, re-queried 2026-10-25 23:05 UTC). @data-planner confirmed that no footprint state has a rule written specifically for telecom lead-sheathed cable (ACC-DP-LEAD-STATE-RULES). Five states have a state hazardous-waste rule that uses the lead toxicity threshold (D008, 5.0 mg/L TCLP):
  * WA: WAC 173-303-090, https://app.leg.wa.gov/WAC/default.aspx?cite=173-303-090 (VERIFIED_STATUTE_TEXT)
  * MN: Minn. R. 7045.0131, https://www.revisor.mn.gov/rules/7045.0131/ (VERIFIED_STATUTE_TEXT)
  * ID: IDAPA 58.01.05, https://adminrules.idaho.gov/rules/current/58/580105.pdf (VERIFIED_STATUTE_TEXT)
  * OR: Oregon DEQ hazardous waste rules, https://www.oregon.gov/deq/Hazards-and-Cleanup/hw/Pages/HW-Rules-Ch.aspx (VERIFIED_OFFICIAL_PAGE)
  * CO: the row is VERIFIED_OFFICIAL_PAGE, but @qa found it cites a CDPHE disaster-recovery guide, not 6 CCR 1007-3 Part 261. **Do not present the CO rule** until ACC-QA-DEF-CO-LEAD-URL is fixed.
  * AZ: **STATE_GAP**. A.A.C. R18-8-261 and R20-5-601 are in the register, but the state sites return HTTP 403 to automated fetch, so they are unverified (human download requested).
* The SOW still carries an environmental-counsel line item for every state. A cited threshold is not a compliance opinion on the carrier's cable.

### 2d. SOW input check against the matrix (v1.1, COO-Q-20261025-0549-4)

Re-queried from `jurisdiction_requirements_cited` on 2026-10-25 23:05 UTC (v1.2). The SOW phases 6-8 use these values. The AZ and CO notice lead-time cells are labeled as the matrix labels them.

| State | Notice lead time | Ticket life | Positive response | Matrix status | citation_url |
| --- | --- | --- | --- | --- | --- |
| WA | 2 business days | 45 calendar days | Required (from 2026-01-01) | VERIFIED_STATUTE_TEXT | https://lawfilesext.leg.wa.gov/law/RCW/RCW%20%2019%20%20TITLE/RCW%20%2019%20.122%20%20CHAPTER/RCW%20%2019%20.122%20.030.htm |
| AZ | 2 working days. **DERIVED**: this is the operator response window in 40-360.22(B); the statute sets no separate excavator notice period | 15 working days | Interactive system | DERIVED_FROM_STATUTE (notice lead-time row) | https://www.azleg.gov/ars/40/00360-22.htm |
| CO | The operator marks within 2 business days, not counting the notice day (103(4)(a)(I)). The verified excerpt does not state a minimum excavator notice period: **GAP**, confirm with Colorado 811 | 30 calendar days | Required | VERIFIED_STATUTE_TEXT (marking window only) | https://content.leg.colorado.gov/sites/default/files/images/olls/crs2024-title-09.pdf |
| MN | 48 h excl. weekends/holidays | 14 calendar days | Not required | VERIFIED_STATUTE_TEXT | https://www.revisor.mn.gov/statutes/cite/216D/full |
| OR | 2 business days | 30 calendar days | Not required | VERIFIED_STATUTE_TEXT (notice); VERIFIED_OFFICIAL_PAGE (ticket life, positive response) | https://www.oregonlegislature.gov/bills_laws/ors/ors757.html ; https://digsafelyoregon.com/wp-content/uploads/2026/03/2026-Addendum-to-the-Oregon-Standards-Manual_Final.pdf |
| ID | 2 business days | 28 calendar days (4 weeks) | Not required by statute | VERIFIED_STATUTE_TEXT | https://legislature.idaho.gov/statutesrules/idstat/Title55/T55CH22/SECT55-2205 |

Lead-sheathed cable (v1.2): the register now has 69 rows, 66 of them verified. ACC-DP-LEAD-STATE-RULES added 14 lead_cable rows. Five state cells now cite state hazardous-waste rules, and only AZ is STATE_GAP (see §2c; the CO citation is being corrected).

### 2e. Field line-item pricing check (v1.2, answers COO-Q-20261025-1750-5)

**Verdict: the SOW template does not yet price the field work.** It sizes phases and locate tickets (§2b). It has no unit costs for:
* the removal method (aerial, buried or conduit pull)
* ROW and municipal permits
* traffic control
* lead-sheath sampling, chain of custody or disposal
* salvage-vendor contracting

No table in `cdm_tmforum.copper_retirement` has a sheath-type, placement-method, permit or traffic-control column. An `information_schema.columns` search on 2026-10-25 23:05 UTC found matches only in the legacy synthetic `state_puc_jurisdiction_requirements.local_row_permit_required` flag. The table below lists every line item with its state today.

| SOW phase | Line item | Unit | Value in accelerator | Source or label | Backing table.column |
| --- | --- | --- | --- | --- | --- |
| 3 | FCC filing fee | $/application | $375 low / $1,445 high | FCC 24-137, https://docs.fcc.gov/public/attachments/FCC-24-137A1.pdf | `roi_calculator_assumptions` param `regulatory_filing_cost_per_wc` |
| 3 | Counsel and state filing cost | $/wire center | NULL | PARTNER_DISCOVERY_INPUT (DEC-ROI-FILING-COST) | `retirement_cost_per_wire_center.regulatory_filing_cost` |
| 4 | Customer migration | $/customer | $845K in total on the demo plant | **SYNTHETIC** | `retirement_cost_per_wire_center.customer_migration_cost` |
| 5 | ROW / municipal permit | $/permit, plus lead time | not modelled | PARTNER_DISCOVERY_INPUT (local) | none |
| 5, 8 | Traffic control | $/crew-day | not modelled | PARTNER_DISCOVERY_INPUT | none |
| 6 | Locate coordination | $/ticket | not modelled; ticket counts only (§2b) | PARTNER_DISCOVERY_INPUT | none |
| 7 | Lead TCLP sampling | $/sample | not modelled. The 5.0 mg/L D008 threshold is cited: https://www.ecfr.gov/current/title-40/chapter-I/subchapter-I/part-261/subpart-C/section-261.24 | PARTNER_DISCOVERY_INPUT | none |
| 7 | Lead chain of custody and hazardous disposal | $/ton | not modelled | PARTNER_DISCOVERY_INPUT (environmental counsel) | none |
| 8 | Removal, aerial | $/ft | not modelled by method. A synthetic per-wire-center lump sum covers all methods ($3.98M in total) | **SYNTHETIC** | `retirement_cost_per_wire_center.equipment_removal_cost` |
| 8 | Removal, buried / conduit pull | $/ft | not modelled by method (same lump sum) | **SYNTHETIC** | same |
| 8, 9 | Copper extraction cost benchmark (UK) | GBP/tonne Cu | 2,800 | Ofcom, https://www.ofcom.org.uk/siteassets/resources/documents/about-ofcom/foi/2025/july/copper-telecoms-cable-infrastructure-estimates.pdf | `roi_calculator_assumptions` param `extraction_cost_gbp_per_tonne` |
| 9 | Salvage labor, haul and processing | $/lb Cu | 1.00 / 2.00 / 3.00 | **SYNTHETIC** (partner input) | `roi_calculator_assumptions` param `salvage_cost_usd_lb` |
| 9 | Recovery rate | fraction | 0.50 / 0.70 / 0.85 | **SYNTHETIC** (partner input) | `roi_calculator_assumptions` param `salvage_recovery_rate` |
| 9 | Copper reference price | $/lb | 5.25 / 6.56 / 7.88 | IMF PCOPPUSDM, https://fred.stlouisfed.org/series/PCOPPUSDM | `roi_calculator_assumptions` param `copper_price_usd_lb` |
| 9 | Copper mass | lb per 1,000 ft of conductor | 0.765 (26 AWG) to 3.9 (19 AWG) | NIST Handbook 100, https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf | `roi_calculator_assumptions` param `cu_lb_per_kft_conductor` |
| 9 | Salvage vendor contracting | % of the reference price, terms | not modelled | PARTNER_DISCOVERY_INPUT | none |

Cited: 5 items (FCC fee, Ofcom extraction benchmark, IMF price, NIST mass, the D008 threshold). Synthetic: 5 items. Not modelled: 7 field items.

**Lead-sheathed vs PIC cable:** the salvage model has a single cable class. `v_roi_sensitivity` uses a 24 AWG net value per kpair-ft and one `salvage_cost_usd_lb`. It does not separate lead-sheath handling cost or recovery. This is a GAP, assigned to ACC-DA-FIELD-COST-LINES.

**How the AZ STATE_GAP is priced:** it becomes a per-state environmental-counsel line plus TCLP sampling. Both are partner inputs, and no state compliance is claimed (§2c). The five cited states get the same line items; they cite the threshold, but counsel still has to confirm how it applies.

**External OSP/SME reviewer:** none has been named. The CEO ask was first filed on 2026-10-24 (status_updates id 113) and is repeated in every @pm rollup as ask D.

Follow-ups:
* ACC-DA-FIELD-COST-LINES (@data-analyst): add these rows as `param_group = 'field_cost'`, and add a sheath-type split to `v_roi_sensitivity`.
* ACC-DP-FIELD-COST-SOURCES (@data-planner): find official public unit-cost benchmarks, such as state DOT bid tabulations. Only official URLs; nothing invented.

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

### 3a. Slide one for a customer CFO (value case, v0.7)

> **"Copper retirement is an operating-cost and risk program. Salvage pays for removal, not for the program."**
>
> 1. **The prize is opex.** AT&T estimated its full-year 2024 direct expense for its entire legacy copper footprint at **$6B a year**: about 60% geographic costs (power, maintenance, real estate) and 40% customer costs (installation, care). Excludes capex and legacy IT. Source: AT&T 2024 Analyst & Investor Day, slide p.58 — https://investors.att.com/~/media/Files/A/ATT-IR-V2/reports-and-presentations/2024-analyst-day-with-notes.pdf
> 2. **Fiber costs less to run.** AT&T: "the cost for us to maintain a fiber subscriber is 35% less than copper subscribers" (transcript p.10) — https://investors.att.com/~/media/Files/A/ATT-IR-V2/reports-and-presentations/transcript-2024-12-03.pdf . Analysys Mason (2022, p.35, citing the Fiber Broadband Association, 2020): FTTH opex is 50% to 63% lower per home passed than HFC and DSL — https://www.analysysmason.com/contentassets/b891ca583e084468baa0b829ced38799/main-report---infra-investment-2022.pdf
> 3. **Salvage is a cost offset.** At the IMF Sep-2026 copper price (https://fred.stlouisfed.org/series/PCOPPUSDM) and NIST copper mass per foot (https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf), recovered copper nets about **$2.25 to $6.88 per lb** after removal cost (`v_roi_sensitivity`, 27 cases). It offsets removal; it does not fund the program.
> 4. **The accelerator's job** is to sequence wire centers so opex comes out early: lowest regulatory friction, highest opex per line, fiber-ready first.

All three sources were fetched (HTTP 200) and the quoted text located in the PDFs on 2026-10-24 by @pm. These are **carrier-level and industry benchmarks, not a per-line figure for the customer**. The customer's own copper O&M per line is a discovery input (`roi_calculator_assumptions.opex_saved_per_line_year` = PARTNER_DISCOVERY_INPUT). Apply the 35% to 63% reduction range to that number.

**The single transferable claim (v0.7):** fiber costs 35% to 63% less to operate than copper (AT&T 35%, transcript p.10; Analysys Mason/FBA 50-63%, p.35; URLs above). It is stored as `roi_calculator_assumptions.opex_reduction_pct_fiber_vs_copper` (0.35 / 0.50 / 0.63, with `source_url`). The slide shows **no demo-dataset payback, NPV or program total**.

**Discovery inputs that turn the claim into a carrier-specific number** (all partner inputs; none of them come from public sources):
1. Working copper lines per wire center in wave 1 (from plant inventory).
2. Copper O&M cost per working line per year, before reduction: maintenance, trouble tickets, truck rolls, power, pole and conduit lease. The demo placeholder `opex_saved_per_line_year` is **synthetic** (120 / 200 / 300 USD).
3. One-time cost per line, ex fiber: removal labor $/ft, customer migration $/customer, and regulatory filing cost per wire center (actual counsel and filing fees).
4. The salvage buyer's recovery rate and terms vs the IMF reference price.
5. Real estate freed (central offices, huts) and the carrier's WACC and planning horizon.

Carrier result = lines x O&M per line x 35-63%, compared with lines x one-time cost per line minus salvage.

**Slide query** (renders the demo method, not a sales number): `SELECT MEASURE(\`Working Copper Lines\`), MEASURE(\`Annual Opex Savings per Line USD\`), MEASURE(\`Annual Opex Savings USD\`), MEASURE(\`One-Time Cost ex Fiber USD\`), MEASURE(\`Payback Months ex Fiber Build\`) FROM cdm_tmforum.copper_retirement.copper_partner_value`. On 2026-10-25 06:00 UTC it returned 3,433 lines, $100/line/yr, $343,300/yr, $10,506,414 and 361.8 months. On 2026-10-25 23:05 UTC, after ACC-DA-FIXFILING NULLed the filing cost, it returns 3,433 lines, $343,300/yr, $4,823,914 and 163.2 months.

### 3b. Demo-dataset numbers (synthetic operational inputs; `copper_partner_value` / `v_roi_sensitivity`, 103 wire centers, 2026-10-25)

**WITHDRAWN (2026-10-25):** the v0.4-v0.6 "~17 months payback ex-fiber" and "10-yr NPV +$13.8M ex-fiber". Both used a synthetic $2.63M/yr opex allocation (about $75K per impacted customer per year), which was not plausible. Do not reuse them.

| Metric | Value | Basis |
| --- | --- | --- |
| Copper in place / recoverable | 34.0K lb / 23.8K lb | NIST AWG pair-ft method on **synthetic** plant |
| Gross salvage | $156K | IMF PCOPPUSDM 2026-09 $6.5649/lb (real price) |
| Decommission cost | $3.98M | **Synthetic** |
| Net salvage | -$3.82M | Gross salvage minus decommission |
| Working copper lines | 3,433 | **Synthetic** plant |
| Annual opex savings | $343K/yr base (range $144K-$649K) = $100 per line per yr (range $42-$189) | **Synthetic** O&M per line x cited 35/50/63% reduction |
| One-time cost ex fiber | $4.82M as of 2026-10-25 23:05 UTC (decommission $3.98M + migration $0.85M; the filing cost is NULL after ACC-DA-FIXFILING). It was $10.51M while it included the withdrawn $5.68M filing line | **Synthetic**. The filing cost (a flat $55K per wire center) had no source (COO-Q-20261025-0549-1). Decision DEC-ROI-FILING-COST (@pm, 2026-10-25): the regulatory filing and compliance cost per wire center is a PARTNER_DISCOVERY_INPUT. It is set to NULL in `retirement_cost_per_wire_center` (ACC-DA-FIXFILING, @data-engineer), and the demo one-time cost is shown ex filing until the partner supplies its counsel and filing costs |
| Payback ex fiber | 163.2 months on the metric view `copper_partner_value`, whose one-time cost of $4.82M includes the synthetic $3.98M decommission lump. 25.7 months on the `v_roi_sensitivity` base case (13.6 to 61.3 months across the opex cases), which leaves out that lump and nets salvage at `salvage_cost_usd_lb` instead. The two views use different cost bases and are **not reconciled**, so neither is a sales number. @data-analyst is reconciling them to one definition (COO-Q-20261025-1750-1) | Shown only to demonstrate the method |
| Fiber build | $148.3M | **Synthetic**; justified by fiber revenue, which is not modelled |

How to present this: it shows the **method** on synthetic data. It is not a forecast and not a sales number. The 3,433-line demo plant is too small, and its synthetic one-time costs too large (about $3,015 per line vs $100/yr saved), to show a payback. Show the per-line formula from §3a and fill it in live with the carrier's discovery inputs. The NPV is removed until the carrier supplies its WACC. **Partner validation:** no partner or carrier has validated this narrative yet (CEO ask D, SME reviewer).

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
* Oregon one-call ticket life: 30 days, effective 2026-01-08, per the OUNC 2026 Addendum (§2a). The OAR text itself is bot-blocked, so confirm it with the carrier's Oregon locate coordinator. ID is verified at 4 consecutive weeks (Idaho Code 55-2205). Confirm the WA positive-response rule (RCW 19.122.030(5)) with the carrier's locate coordinator.
* State lead-cable disposal rules and whether the RCRA scrap-metal exclusion applies to the carrier's lead-sheathed cable. Needs the carrier's environmental counsel (phase 7).
* State scrap-metal dealer licensing and record-keeping rules for each salvage buyer state (phase 9).
* State PUC copper-retirement / discontinuance notice rules on top of the federal rules (phases 3-4).
* Pole-attachment and joint-use agreement terms for aerial removal (phase 8).
* The carrier's actual salvage recovery rate, removal labor $/ft, and opex per retired wire center (§3 inputs).
* A named carrier field-ops SME to sign off the phase durations in §2.

## 5. Demo script (merged from DEMO-RUNBOOK.md §2/§6 and demo_kpi_cheat_sheet.md)

Run the demo in the **unified accelerator app** (evolved `retirement-plan`). The standalone regulatory-assistant and dig-triage apps were deleted on 2026-10-24 (asset_ledger 97, 108). Regulatory and Dig Triage are tabs in the unified app. The Map/Risk tab code is committed in the unified app (ACC-APP-PORT-MAP), but it is not deployed: agents cannot run `databricks apps deploy`, so this is a CEO action. Until then Map/Risk runs in the standalone `copper-map` app. The Commodity & Value tab code was ported on 2026-10-25 (it uses the real IMF series). Like Map, it waits on the same CEO redeploy, so until then Commodity runs in `commodity-dashboard`. **Pre-req:** the unified app's service principal needs UC read grants (ACC-PM-APP-SP-GRANTS, CEO action). Without them every tab shows an error state, so check this before any customer demo. **As of 2026-10-25 23:05 UTC the grants are still missing: SHOW GRANTS on `cdm_tmforum.copper_retirement` has no row for SP d96a80a5. Use the §5a fallback.**

**T-10 to T-1 warm-up**
1. Warm the SQL warehouse: `SELECT COUNT(*)` on `gold_wire_center_scorecard`, `gold_device_risk_predictions`, `gold_circuit_revenue_at_risk` (all in `cdm_tmforum.copper_retirement`).
2. Warm serving endpoint `copper-retirement-risk` (scale-to-zero, 60-90 s cold start). Send one request with all 39 V5 features; the feature contract is in the model card (ACC-ML-MODEL-CARD).
3. Open the Map tab: H3 hexagons coloured by risk; click a hexagon to see device count, risk score and customer count; filter by state and risk tier.
4. Open the unified app **Regulatory** tab (`#regulatory`) and ask "What notice must an ILEC give before retiring copper?". Expected answer: 90 days direct notice (15 if no customers), citing FCC 26-19 / 47 CFR 51.333 with the official URL (see §2 phase 3). Never demo an answer without a citation.
5. Final check: warehouse RUNNING, endpoint READY, Map and Regulatory tabs rendering live data (not error states), and the Regulatory answer shows [S#] official-URL chips.

**Beat 1 — "Where is our copper and what is the risk of touching it?"** Map US view, zoom to a region, click a hexagon, filter to critical.
**Beat 4 — "Are we clear on regulations everywhere we touch?"** Ask the federal question, then a footprint-state 811 question (WA/AZ/CO/MN/OR/ID), and show the citations. **Gate:** Beat 4 can run live from the unified app Regulatory tab, which uses real chunks only and shows citations. Present only answers that show [S#] official-URL chips, and do not present matrix rows that are not verified (§2 phase 2). @qa signed off ACC-QA-REG-CITATIONS on 2026-10-25: 68/68 matrix rows have a reachable `citation_url`, numeric values were checked verbatim against the cited text, and 20/20 sampled TVF answers cite registered sources. Open items: ACC-QA-DEF-RAG-ALLOWLIST (the scorer accepts one unregistered URL) and ACC-QA-RAG-VS-RETEST (the VS path, after the index recreate). Fallback: show the cited 811 table in §2a.

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
| Net salvage (demo, synthetic) | -$3.82M. Opex is $100 per line per yr (cited 35-63% reduction). No demo payback is shown as a sales number (see §3b) | `copper_partner_value` / `v_partner_value_wire_center` |

### 5a. Demo fallback if a partner demo ran Monday 2026-10-26 (dated 2026-10-25 06:10 UTC; re-date before each use)

| Beat / tab | What is shown | From which app | Data | Status |
| --- | --- | --- | --- | --- |
| Beat 1 Map/Risk | Risk map, wire-center scorecard, KPIs | Standalone `copper-map` (Dash), ACTIVE | Synthetic plant, V5 model scores | **LIVE** in copper-map. The unified Map tab code is committed (routes/map.js, tabs/map/MapTab.tsx) but is not deployed and has no SP grants. **Not shown** in the unified app |
| Plan | Wave schedule, budget, milestones, cited regulatory checklist | Unified `retirement-plan` | UC only (v0.9): `gold_wave_schedule`, `silver_budget_allocation`, `retirement_milestones` (927 rows), and a checklist built from `jurisdiction_requirements_cited` x wave schedule (1,854 items across 103 wire centers, 0 without an official URL; non-verified items are labeled as flagged gaps) | **NOT SHOWN.** The code is fixed (ACC-APP-PLAN-LAKEBASE-READS; all 5 statements succeeded on warehouse 9cd919d96b11bf1c on 2026-10-25), but it needs the CEO redeploy and the SP grants |
| Dig Triage | 811 ticket triage | Unified app | stg_811_dig_ticket | **NOT SHOWN live.** It needs the redeploy and the SP grants. After the redeploy, a missing grant shows 'Data access pending' (not 'Incident not found'), and Report Incident is labeled 'DEMO ONLY - NOT SAVED' (ACC-DES-DEF-TRIAGE-STATES). Use screenshot slides until then (@app-developer to capture after the grants land) |
| Beat 4 Regulatory | Cited Q&A + jurisdiction matrix | Unified app, needs SP grants | 1,719 real chunks via TVF | **NOT LIVE** until the grants land. Fallback: present the §2 phase 3 and §2a cited tables from this playbook, and run the notebook query `SELECT * FROM cdm_tmforum.copper_retirement.search_regulatory_chunks('copper retirement notice', 5)` live on a warehouse, showing `source_url` |
| Commodity | Copper price, salvage | Standalone `commodity-dashboard`, ACTIVE | Real IMF price + synthetic volumes | **LIVE** in commodity-dashboard |
| Value (§3a) | Cited 35-63% claim + per-line formula | Slide / this playbook | Cited benchmarks | **LIVE** (static slide) |

**Deletion gate (binding, @pm 2026-10-25):** `copper-map` and `commodity-dashboard` must **not** be stopped or deleted until (a) the CEO has deployed `retirement-plan` with the new tabs, (b) the SP `d96a80a5-cf49-4947-b518-164cd950f872` has the UC grants, and (c) @app-developer records proof in the port task's `status_notes`: a screenshot or curl of the corresponding unified tab returning rows. ACC-APP-PORT-MAP and ACC-APP-PORT-COMMODITY carry this gate.

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

This comes from reading the 5 active bundle resources (the `databricks.yml` include list now adds `seed_synthetic_sources.job.yml`), `pipeline/*.sql` (11 files) and `apps/retirement-plan` source. It is not a live deploy. Until ACC-QA-FRESH-DEPLOY passes, treat a clean `partner` deploy as **not yet proven**.

| # | Dependency | Read by | In bundle? | Gap / owner |
| --- | --- | --- | --- | --- |
| 1 | TMF SID source schemas `tmf_enterprise` (physical_device, work, project, milestone, budget, workforce_*), `tmf_resource.device_service_allocation`, `tmf_service.customer_facing_service` | pipeline bronze/silver, Plan tab queries | Yes (seed job) | Run `databricks bundle run -t partner seed_synthetic_sources_job` after deploy. It seeds every table, labeled SYNTHETIC (table comment plus `copper.seed.synthetic=true`), then refreshes the pipeline. Replace with the partner's real sources when available. ACC-DE-SEED-JOB is completed; the live proof is pending ACC-QA-SEED-JOB-SMOKE. |
| 2 | `oracle_erp_source.*` (ra_billed_circuit_rates, ra_customer_trx_all, revenue_recognition_schedule), `ironclad_clm_source.contract_record` | silver_revenue_recognition_constraints, silver_contract_constraints, gold_circuit_revenue_at_risk | Yes (seed job) | Same as #1. |
| 3 | `copper_plant_wire_center_jurisdiction`, `dig_safe_incident`, `contractor_performance` in `${schema_name}` | silver_copper_plant_enriched, bronze_dig_safe_incidents, gold_contractor_scorecard | Yes (seed job) | Same as #1. The 6 legacy footprint states only (DEC-DSI-FOOTPRINT). |
| 4 | `provable_resilience_intelligence.stg_811_dig_ticket` | Dig Triage tab | Yes (seed job) | This comes from another project's schema in the reference workspace. The seed job creates a synthetic copy. The partner can swap in real 811 data. |
| 5 | Regulatory corpus: volume `regulatory_source_docs`, `regulatory_source_register`, `regulatory_doc_chunks`, TVF `search_regulatory_chunks`, `jurisdiction_requirements_cited` | Regulatory tab | No | The ingest/parse code exists but is not a bundle job. Follow-up after ACC-DE-SEED-JOB. |
| 6 | Hard-coded `cdm_tmforum.*` in app SQL (server/databricksSQL.js, routes/triage.js, tabs/triage/lib/triageApi.ts, config/queries/*.sql) | unified app | — | The app ignores `--var catalog_name`. Fix in ACC-QA-DEF-APP-CATALOG (@app-developer). |
| 7 | Warehouse id `9cd919d96b11bf1c` hard-coded in `apps/retirement-plan/app.yaml` | unified app | Partly: the bundle attaches `sql-warehouse` from `${var.warehouse_id}` | app.yaml should read the `sql-warehouse` resource with `valueFrom`. Fix in ACC-DEVOPS-RM-REGASSIST-BUNDLE (@devops). |
| 8 | Serving endpoints `copper-retirement-risk` and LLM `databricks-claude-sonnet-4-5` | Map/Risk, Regulatory tabs | No (prerequisite) | The partner runs the retrain template (`beat1_risk_model_walkthrough`). The LLM must exist as a pay-per-token endpoint in the partner region. |
| 9 | Vector Search endpoint + index | Regulatory tab (target design) | No (prerequisite) | Interim retrieval uses the Delta TVF (#5), so VS is optional until ACC-REG-VS-RESYNC. |
| 10 | App service-principal UC grants (USE CATALOG/SCHEMA, SELECT, EXECUTE) | all tabs | Partly | `-t partner` now grants USE_SCHEMA/SELECT/EXECUTE on `${catalog_name}.${schema_name}` to the unified app SP (and USE_SCHEMA/SELECT to the task-board SP) on deploy, and the app gets CAN_USE on the warehouse and CAN_QUERY on `${llm_endpoint}` as app resources (ACC-DEVOPS-BUNDLE-SP-GRANTS). **Post-deploy, catalog owner:** `GRANT USE CATALOG ON CATALOG <catalog>` and `GRANT USE SCHEMA, SELECT ON SCHEMA <catalog>.provable_resilience_intelligence` to the app SP (commands in the databricks.yml header). The reference workspace grants are still a CEO action (ACC-PM-APP-SP-GRANTS). |
| 11 | Lakebase project + `copper_app` schema DDL | copper-task-board, app write-back | No (prerequisite) | DDL script not packaged. The sync job is disabled (ACC-CREATE-LAKEBASE-SYNC-SCRIPT). |

Shortest path to a provable one-command partner deploy: ACC-DE-SEED-JOB (#1-4, done), ACC-QA-DEF-APP-CATALOG (#6, done; Plan queries follow in ACC-APP-PARAM-PLAN-QUERIES), ACC-DEVOPS-RM-REGASSIST-BUNDLE (#7, done; live resource attach in ACC-DEVOPS-APP-WH-RESOURCE), then ACC-QA-SEED-JOB-SMOKE and ACC-QA-FRESH-DEPLOY (both need a sandbox workspace or a CEO-approved scratch catalog).

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
