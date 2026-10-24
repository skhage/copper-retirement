# Copper Retirement Solution Accelerator — Partner Playbook (DRAFT v0.2)

> Owner: @pm. Task: ACC-DOCS-PARTNER-PLAYBOOK. Status: DRAFT v0.2 (2026-10-24 09:15 UTC). Sections 5-7 now absorb DEMO-RUNBOOK.md, DEMO-ROLLBACK-RECOVERY.md, DEMO-ENV-FREEZE-CHECKLIST.md and demo_kpi_cheat_sheet.md (content merged 2026-10-24; the 4 source files are **not yet deleted**. Workspace deletion by a scheduled agent was blocked, so it is pending CEO approval. Originals are also in git history on origin/main of github.com/skhage/copper-retirement, commits a6aa6d0 and 946b559). README.md is kept as the repo root readme and now points here.
>
> Rule for this document: every regulatory statement carries an official URL. Anything not yet verified is marked **GAP** and is not to be presented to a customer as fact. Durations are planning assumptions for SOW sizing, not regulatory requirements, and must be validated by the partner's field-operations lead.

## 0. Data disclosure
The demo dataset (Lakelink Fiber) is **synthetic**. Device, customer, wire-center, contractor and dig-incident data are generated. Regulatory content is being replaced with real downloaded sources (R1). Copper price is now a real public series: IMF Primary Commodity Prices, copper (PCOPPUSDM, monthly, USD/metric ton) in `cdm_tmforum.copper_retirement.copper_commodity_price_official` (417 rows; `source_url` = https://fred.stlouisfed.org/series/PCOPPUSDM). LME (https://www.lme.com/en/metals/non-ferrous/lme-copper) is licensed and kept as a reference only. Copper volumes, plant, customers and costs remain **synthetic**.

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
| 2 | Wave planning | 2-3 weeks | Partner PM, carrier engineering + regulatory affairs | Retirement waves, customer migration plan, jurisdiction requirements matrix per wave | Jurisdiction matrix built from state PUC rules — **GAP** until ACC-REG-JURISDICTION-MATRIX is complete |
| 3 | Regulatory notices and filings | Driven by notice periods (see source) | Carrier regulatory affairs, counsel | Copper retirement direct notices, Section 214 discontinuance application where service is discontinued, state filings | Direct notice of planned copper retirement at least 90 days before implementation (15 days if the copper serves no customers): FCC 26-19 (adopted 2026-03-26, published 91 FR 20913, 2026-04-20), Appendix A, revised 47 CFR 51.333(a)(2) — https://docs.fcc.gov/public/attachments/FCC-26-19A1.pdf . FCC 26-19 eliminates the FCC filing and Bureau public-notice/objection process for copper retirements; the ILEC still posts public notice and gives direct notice. Section 214 discontinuance: 47 CFR 63.71 — https://www.ecfr.gov/current/title-47/section-63.71 ; FCC 26-19 applies a 31-day automatic grant period to all discontinuance applications (Section III.B). **Effectiveness:** the order said these amendments (51.329, 51.333, 63.60, 63.62, 63.63, 63.71, 63.602) would not take effect until OMB PRA review (para 120). WCB announced OMB approval (control nos. 3060-0149, 3060-0741) and the amendments are **effective 2026-10-15**: 91 FR 62334, FR Doc. 2026-20192, published 2026-10-01 — https://www.federalregister.gov/documents/2026/10/01/2026-20192/wc-docket-nos-25-208-25-209-fcc-26-19-fr-id-370342-reducing-barriers-to-network-improvements-and (verified via federalregister.gov API, `effective_on` = 2026-10-15, on 2026-10-24). Notices served before 2026-10-15 fall under the prior rules (FCC 17-154 https://docs.fcc.gov/public/attachments/FCC-17-154A1_Rcd.pdf , FCC 18-74 https://docs.fcc.gov/public/attachments/FCC-18-74A1_Rcd.pdf ). **GAP:** eCFR may lag the amendment, so check the current eCFR text before quoting rule wording; state notice requirements per state |
| 4 | Customer migration | Parallel to phase 3, 6-12 weeks | Carrier care/sales, field install | Customers migrated to fiber/alternative service, migration KPI tracking | Customer notice obligations tied to discontinuance — see 47 CFR 63.71 above; state consumer rules **GAP** |
| 5 | Permits and right-of-way | 2-8 weeks, jurisdiction dependent | Partner permitting coordinator, carrier outside-plant | ROW / municipal permits, traffic control plans | Utilities on federal-aid highway ROW: 23 CFR Part 645 — https://www.ecfr.gov/current/title-23/chapter-I/subchapter-G/part-645 . Municipal permit rules **GAP** (local) |
| 6 | 811 locates and dig safety (buried plant) | Wait period set by state one-call law, plus ticket renewals per wave | Excavation contractor, carrier locate coordinator | One-call tickets per work area, positive response confirmation, dig-triage risk scoring (Dig Triage tab) | Locate underground installations before excavation: OSHA 29 CFR 1926.651(b) — https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.651 . Use one-call and wait for marks before excavating near pipelines: PHMSA 49 CFR Part 196 — https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-D/part-196 ; state damage-prevention programs: 49 CFR Part 198 — https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-D/part-198 . Industry practice: CGA Best Practices v21 — https://bestpractices.commongroundalliance.com/Portals/1/Best%20Practices%20Guide%20Version%2021%20PDF%20Download.pdf . Excavation protection: OSHA 29 CFR 1926 Subpart P (1926.651 above). Per-state notice, tolerance and ticket life: see §2a (sourced from `regulatory_source_register`; all rows still `unverified_detail` until ACC-REG-DOWNLOAD hashes the statute text) |
| 7 | Lead-sheathed cable assessment and handling | 1-3 weeks per wave (sampling, plan) | Environmental consultant, safety officer, removal contractor | Lead-sheath inventory flag per span, worker exposure plan, handling and disposal plan | Worker lead exposure in construction: OSHA 29 CFR 1926.62 — https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.62 . EPA has run response actions on lead telecom cable (Louisiana Lead Cable site) — https://response.epa.gov/site/site_profile.aspx?site_id=16204 . Scrap metal recycling exclusions under RCRA: 40 CFR 261.4 and 261.6 — https://www.ecfr.gov/current/title-40/chapter-I/subchapter-I/part-261/section-261.4 , https://www.ecfr.gov/current/title-40/chapter-I/subchapter-I/part-261/section-261.6 . **GAP:** applicability of the scrap-metal exclusion to lead-sheathed cable and state disposal rules must be confirmed by environmental counsel |
| 8 | Field removal — aerial vs buried | 4-12 weeks per wave | Removal contractor, carrier outside-plant inspector | Spans removed, pole attachments cleared, restoration sign-off | Telecom worker safety (incl. aerial work): OSHA 29 CFR 1910.268 — https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.268 . Pole-attachment / joint-use agreements **GAP** (contractual) |
| 9 | Salvage, chain of custody and sale | 2-6 weeks per wave | Salvage buyer, carrier asset recovery, finance | Weighed lots, chain-of-custody records, buyer settlement vs reference price, recovery report | Reference price: LME copper (https://www.lme.com/en/metals/non-ferrous/lme-copper, licensed data). State scrap-metal dealer and record-keeping laws **GAP** |
| 10 | Decommission and close-out | 2-4 weeks | Partner PM, carrier finance | Inventory/records retired, opex and real-estate savings booked, value report from partner value metric view | None (internal) |

Validation status: drafted by @pm from official sources above on 2026-10-24. **Not yet validated by a carrier or partner field-operations SME.** CEO was asked to name a reviewer on 2026-10-24 (status_updates id 113); no reviewer named as of 2026-10-24 09:00 UTC. Re-asked in today's rollup.

### 2a. 811 one-call requirements — footprint states (planning use only)

Source: `cdm_tmforum.copper_retirement.regulatory_source_register` (`topic = 'one_call_811'`). Every row is `verification_status = unverified_detail`: the statute URL opened (HTTP 200) but the numbers have not yet been confirmed against downloaded statute text. Do not present them to a customer as fact until @qa clears ACC-QA-REG-CITATIONS.

| State | register source_id | Statute (official URL) | Notice before digging | Tolerance zone | Ticket / mark life | Open item |
| --- | --- | --- | --- | --- | --- | --- |
| WA | WA-811-RCW19.122 | RCW 19.122 — https://apps.leg.wa.gov/rcw/default.aspx?cite=19.122&full=true | 2 business days | 24 in either side | 45 days per CGA state page only — **GAP** | Positive-response effective date unverified |
| AZ | AZ-811-ARS40-360 | A.R.S. 40-360.22 — https://www.azleg.gov/ars/40/00360-22.htm | 2 working days | 18 in | 15 working days | Subsection cites unconfirmed |
| CO | CO-811-CRS9-1.5 | C.R.S. 9-1.5 — https://content.leg.colorado.gov/sites/default/files/images/olls/crs2023-title-09.pdf | 2 business days | 18 in | 30 calendar days after locate due date | 2023 compilation; confirm current year |
| MN | MN-811-216D | Minn. Stat. 216D — https://www.revisor.mn.gov/statutes/cite/216D/full | 48 hours excl. weekends/holidays | 24 in (+/- 2 ft) | 14 days (6 months with periodic refresh, Minn. R. 7560) | Confirm current Minn. R. 7560 |
| OR | OR-811-ORS757 | ORS 757.542-757.562; OAR 952-001 — https://www.oregonlegislature.gov/bills_laws/ors/ors757.html | 2 business days | 24 in (OAR 952) | **GAP** (only a 1995 archive found; do not cite) | ACC-REG-GAPS-1024 |
| ID | ID-811-IC55-22 | Idaho Code 55-2201 et seq. — https://dopl.idaho.gov/dpb/dpb-statutes-rules-and-guidance/ | 2 business days | 24 in | **GAP** | legislature.idaho.gov blocked to research tool |

SOW sizing rule of thumb: plan each work area for notice period + ticket refreshes across the field-removal phase (phase 8 can run 4-12 weeks, which is longer than the ticket life in every state above, so expect at least one renewal per area).

## 3. ROI calculator inputs (to be backed by ACC-DA-VALUE-METRICS)

| Input | Formula / source | Owner |
| --- | --- | --- |
| Copper recoverable (lbs) | sum(cable length x lbs per foot by gauge/pair count) from copper plant tables | @data-analyst |
| Salvage value ($) | copper lbs x reference price x buyer recovery % (net of lead-sheath handling) | @data-analyst |
| Opex savings ($/yr) | maintenance, trouble tickets, power for retired wire centers | @data-analyst |
| Real-estate value ($) | central offices / huts freed | partner input |
| Program cost ($) | sum of SOW phase costs above | partner input |
| Payback (months) | program cost / (monthly opex savings + salvage proceeds amortized) | @data-analyst |

**Current numbers (demo data, from metric view `cdm_tmforum.copper_retirement.copper_partner_value`, ACC-DA-VALUE-METRICS, 2026-10-24):**

| Metric | Value | Basis |
| --- | --- | --- |
| Recoverable copper | 7.20M lbs | **Synthetic** plant volumes |
| Reference price | $6.5649/lb | IMF PCOPPUSDM, 2026-09 — https://fred.stlouisfed.org/series/PCOPPUSDM (real) |
| Net salvage value | $43.3M | lbs x price x 0.85 buyer recovery rate (**recovery rate has no source yet**) |
| Opex savings | $2.63M/yr | **Synthetic** maintenance/trouble-ticket costs |
| Payback | 0 months excluding fiber build; 521 months including the $148.3M fiber build | Synthetic program cost |

How to present this: these are demo outputs on synthetic plant data, not a carrier forecast. Do **not** put "0-month payback" on slide one. Show the salvage figure as a range from the sensitivity analysis (COO-Q-20261024-0548-2, @data-analyst) and replace the recovery rate, labor $/ft and opex inputs with carrier values in `partner_value_assumptions` during discovery.

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
* State one-call ticket life where the register shows GAP (OR, ID) and confirmation of the WA positive-response rule (§2a).
* State lead-cable disposal rules and whether the RCRA scrap-metal exclusion applies to the carrier's lead-sheathed cable. Needs the carrier's environmental counsel (phase 7).
* State scrap-metal dealer licensing and record-keeping rules for each salvage buyer state (phase 9).
* State PUC copper-retirement / discontinuance notice rules on top of the federal rules (phases 3-4).
* Pole-attachment and joint-use agreement terms for aerial removal (phase 8).
* The carrier's actual salvage recovery rate, removal labor $/ft, and opex per retired wire center (§3 inputs).
* A named carrier field-ops SME to sign off the phase durations in §2.

## 5. Demo script (merged from DEMO-RUNBOOK.md §2/§6 and demo_kpi_cheat_sheet.md)

This is the V1 two-app script (copper-map + regulatory-assistant). In R2 it moves to the unified app tabs (Map/Risk, Plan, Dig Triage, Regulatory, Commodity) per PORT-MAP.md, using the same order.

**T-10 to T-1 warm-up**
1. Warm the SQL warehouse: `SELECT COUNT(*)` on `gold_wire_center_scorecard`, `gold_device_risk_predictions`, `gold_circuit_revenue_at_risk` (all in `cdm_tmforum.copper_retirement`).
2. Warm serving endpoint `copper-retirement-risk` (scale-to-zero, 60-90 s cold start). Send one request with all 39 V5 features; the feature contract is in the model card (ACC-ML-MODEL-CARD).
3. Open the Map tab: H3 hexagons coloured by risk; click a hexagon to see device count, risk score and customer count; filter by state and risk tier.
4. Open the Regulatory tab and ask "What notice must an ILEC give before retiring copper?". Expected answer: 90 days direct notice (15 if no customers), citing FCC 26-19 / 47 CFR 51.333 with the official URL (see §2 phase 3). Never demo an answer without a citation.
5. Final check: warehouse RUNNING, endpoint READY, VS index ready, both tabs rendering.

**Beat 1 — "Where is our copper and what is the risk of touching it?"** Map US view, zoom to a region, click a hexagon, filter to critical.
**Beat 4 — "Are we clear on regulations everywhere we touch?"** Ask the federal question, then a footprint-state 811 question (WA/AZ/CO/MN/OR/ID), and show the citations.

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
| Net salvage value | $43.3M (see §3 caveats) | `copper_partner_value` |

## 6. Deploy and environment baseline (merged from DEMO-ENV-FREEZE-CHECKLIST.md; README.md kept)

Target: one command, `databricks bundle deploy -t <target>` with variables (ACC-DAB-ONE-COMMAND done; validate defects ACC-QA-DEF-DAB-VALIDATE / -PARAMS / -SERVING / -APPS open with @devops). Until those close, a fresh workspace needs the steps below.

| Component | Reference implementation (this workspace) | Partner variable |
| --- | --- | --- |
| Catalog / schema | `cdm_tmforum.copper_retirement` | `catalog`, `schema` |
| Pipeline | `copper-retirement-pipeline` (b52532a2-6398-44ed-b239-9e95cafb745c), serverless, 8 MVs: bronze_copper_devices, bronze_copper_services, bronze_dig_safe_incidents, silver_copper_plant_enriched, silver_device_service_impact, gold_wire_center_scorecard, gold_contractor_scorecard, gold_retirement_executive_summary | — |
| Risk model | `cdm_tmforum.ml_models.copper_retirement_risk` V5 champion (LightGBM, 39 features, AUC 0.986), V4 fallback | `model_name` |
| Serving endpoint | `copper-retirement-risk`, Small, scale-to-zero, inference logging to `risk_model_inference_payload` | `serving_endpoint` |
| Vector Search | endpoint `demo_telco_vs_endpoint` (STANDARD); index `regulatory_doc_chunks_vs_index` on `regulatory_doc_chunks`, `databricks-gte-large-en`, TRIGGERED sync | `vs_endpoint`, `vs_index` |
| Lakebase | project `copper-task-board`, branch `production`, schema `copper_app` (app data) | `lakebase_project` |
| SQL warehouse | Serverless Starter Warehouse 7b65956f30d66feb (backup telco-builders da0dbcd5676d37eb) | `warehouse_id` |
| Apps (R2 target) | unified accelerator app (evolved `retirement-plan`) + internal `copper-task-board` | `app_name` |

Baseline row counts after a clean build (V1 snapshot, synthetic): bronze_copper_devices 2,672; bronze_copper_services 17,655; silver_copper_plant_enriched 2,672; silver_device_service_impact 440; gold_wire_center_scorecard 103; gold_circuit_revenue_at_risk 14,777; gold_contractor_scorecard 10,000; gold_retirement_executive_summary 6; gold_device_risk_predictions 2,672. Lakebase copper_app: device_risk_map 2,672; wire_center_scorecard 103; wire_center_boundaries 1,699; contractor_scorecard 10,000; retirement_plan 200; retirement_milestones 927; dig_incidents 5,000; jurisdiction_requirements 56; commodity_prices 10,482. `regulatory_doc_chunks` (528) and `copper_app.regulatory_documents` (297) are being replaced with real sources in R1, so their counts will change.

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
| 6 Databricks Apps, always on (86 DBU each, $81.70 each) | $490.20 | 2 apps in R2 |
| Vector Search endpoint `demo_telco_vs_endpoint` (shared by 7 indexes) | $48.16 | Yes (1 endpoint) |
| Lakebase `copper-task-board` | $13.05 | copper_app schema only |
| Serving `copper-retirement-risk` (scale-to-zero) | $0.16 | Yes |
| Agent swarm serverless notebook compute (69 copper runs) | $18.15 | No (build-time only) |
| Agent swarm Genie Code usage (estimated pro-rata 69/1,490 conversations of $4,953.93) | ~$229 | No (build-time only) |
| **Total** | **~$799 / week** | |

Retiring commodity-dashboard, copper-map, dig-triage and regulatory-assistant saves $326.80/week (about $46.69/day, about $1,400/month).

**Estimated partner steady-state run cost:** about $1,000/month list. That is 2 apps at about $350/month each, plus VS endpoint about $206/month, Lakebase about $56/month and serving close to $0 idle. SQL warehouse and pipeline refresh costs come on top and depend on usage. Re-measure on the partner's cloud/region.
