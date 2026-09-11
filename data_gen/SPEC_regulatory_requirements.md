# Regulatory Requirements — Synthetic Data Specification

**Task:** P0-DATAGEN-REG
**Author:** @data-engineer | **Date:** 2026-09-11
**Status:** Schema spec complete. Ready for implementation.

---

## Objective

Synthesize two tables and one document corpus that feed the P6-REG regulatory RAG agent and the P3-DLP gold `regulatory_requirements_by_jurisdiction` pipeline target:

1. **`state_puc_jurisdiction_requirements`** — lookup table: one row per US state, encoding copper-retirement notice periods, filing types, and Section 214 applicability.
2. **`fcc_regulatory_document`** — synthetic FCC orders, state PUC dockets, and compliance guidance documents for RAG retrieval grounding.
3. **Companion PDF/text files** — sample FCC docket text stored as files in a UC Volume for Auto Loader ingestion (P1-REG bronze pattern replicating `revenue_assurance.bronze_contract_pdfs`).

---

## Source Material & Domain Grounding

### Corrected FCC 26-19 Facts (BUILD-PLAN.md §0)
- **FCC 26-19** (adopted March 26, 2026) eliminated the **Section 251(c)(5)** network-change disclosure FCC filing and its public-notice/objection process for copper retirement.
- **Section 214(a) discontinuance authorization is still required** when a retirement causes a service discontinuance — the order *streamlined* it (consolidated tech-transition rule, 31-day automatic grants, blanket grandfathering authority, 911-coordination).
- **90-day residential direct written notice** to retail customers remains.
- **180-day state/tribal notice** (to state governor + PUC + tribal governments) — 90 days if no remaining customers on the copper.
- **Consumer protections:** network performance/reliability substantially unchanged, 911/accessibility/cybersecurity standards met, legacy device compatibility (alarms, medical monitors, fax).
- **Backup power:** if copper replaced by non-powered-by-network tech, must offer 8-hour minimum battery backup (moving toward 24-hour).

### Existing Catalog Tables Profiled

| Table | Rows | Relevance | Usable? |
| --- | --- | --- | --- |
| `tmf_enterprise.regulator` | 1K | 42 cols, has `jurisdiction`, `authority_level`, `type`, `compliance_deadline_days` | Names/jurisdictions are random hashes. Unusable for US regulatory data. No state-level US regulators. |
| `tmf_marketsales.policy` | 10K | 45 cols, has `regulatory_reference`, `regulatory_compliance_flag`, `domain_scope` | Random hash names. `domain_scope` has real categories (resource, service, customer, etc). Structure useful as template. |
| `tmf_marketsales.policy_rule` | 100K | 50 cols, has `regulatory_reference`, `regulatory_compliance_flag`, `rule_category`, `rule_type` | Values are random hashes. Schema pattern reusable for notice-rule modeling. |
| `tmf_shared.document` | 10K | 46 cols, has `type` (incl `regulatory_filing` 381 rows, `policy` 450 rows), `nature`, `regulatory_compliance_flag` | Random hash content. `type='regulatory_filing'` exists but content is unusable. Schema is good template for regulatory docs. |
| `revenue_assurance.silver_doc_intelligence_contracts` | 50 | AI-parsed doc pattern via `ai_parse_document` | Reusable RAG architecture for FCC doc parsing. |
| `revenue_assurance.bronze_contract_pdfs` | 50 | Auto Loader PDF ingestion pattern | Reusable for P1-REG bronze FCC doc ingestion. |

### FK Relationships Available
- `tmf_shared.geographic_address.state_or_province` → will contain real US state abbreviations after FIX-COORDINATES
- `tmf_enterprise.regulator.regulator_id` → can FK from jurisdiction requirements to a synthetic FCC/PUC regulator entry
- `tmf_shared.document.document_id` → can FK from FCC docket entries to the document table

---

## Table 1: `state_puc_jurisdiction_requirements`

**Target catalog/schema:** `cdm_tmforum.copper_retirement` (or `cdm_tmforum.tmf_enterprise` if `copper_retirement` schema not yet created)
**Recommended row count:** 56 rows (50 US states + DC + 5 territories: PR, GU, VI, AS, MP)
**Determinism:** Follow `synthetic_assets.py` pattern — `random.Random(seed)`, no wall-clock or network calls.

### Column Specification

| # | Column | Type | Nullable | Description | Value Generation |
| --- | --- | --- | --- | --- | --- |
| 1 | `jurisdiction_id` | BIGINT | NO | PK, auto-increment from 50001 | Sequential |
| 2 | `state_code` | STRING | NO | US state/territory abbreviation (2-letter) | All 50 states + DC + 5 territories |
| 3 | `state_name` | STRING | NO | Full state name | Lookup from state_code |
| 4 | `puc_name` | STRING | NO | Name of state Public Utilities Commission | Realistic names: e.g., "Colorado Public Utilities Commission", "Minnesota Public Utilities Commission" |
| 5 | `puc_short_name` | STRING | NO | Abbreviation | e.g., "CPUC", "MNPUC" |
| 6 | `puc_website_url` | STRING | YES | PUC website URL | Synthetic: `https://puc.{state_code.lower()}.gov` |
| 7 | `governor_notice_days` | INT | NO | Days of advance notice to state governor before copper retirement | Federal baseline: 180 (90 if no remaining customers). Vary ±30 by state for realism (range 150-210). |
| 8 | `puc_notice_days` | INT | NO | Days of advance notice to state PUC | Same baseline as governor (180). Some states require longer (up to 365 for CA, NY). |
| 9 | `residential_direct_notice_days` | INT | NO | Days of direct written notice to residential retail customers | Federal floor: 90. Some states require 120+ (e.g., CA, NY, MA). |
| 10 | `tribal_notice_days` | INT | NO | Days of advance notice to tribal governments | Federal baseline: 180. |
| 11 | `section_214_required` | BOOLEAN | NO | Whether Section 214 discontinuance authorization is needed for copper retirement in this state | Always TRUE (federal requirement). Column exists for explainability in the regulatory agent. |
| 12 | `section_214_streamlined` | BOOLEAN | NO | Whether 31-day auto-grant streamlining applies | TRUE for all post-FCC-26-19 filings. |
| 13 | `section_251c5_filing_required` | BOOLEAN | NO | Whether Section 251(c)(5) network-change FCC filing is required | Always FALSE post-FCC-26-19 (eliminated). Key demo talking point. |
| 14 | `public_notice_required` | BOOLEAN | NO | Whether public notice (website/industry fora) required even without FCC filing | Always TRUE (federal). |
| 15 | `backup_power_disclosure_required` | BOOLEAN | NO | Carrier must offer backup battery option if copper replaced by non-powered tech | Always TRUE (federal). |
| 16 | `backup_power_minimum_hours` | INT | NO | Minimum backup battery hours | Federal: 8. Some states mandate 24 (CA, NY). |
| 17 | `filing_type` | STRING | NO | Primary PUC filing mechanism for copper retirement | Categorical: `tariff_amendment`, `informational_filing`, `application`, `notification_only`, `no_state_filing` |
| 18 | `e911_coordination_required` | BOOLEAN | NO | Must coordinate with 911 service providers | Always TRUE (federal FCC 26-19 addition). |
| 19 | `interconnecting_carrier_notice_required` | BOOLEAN | NO | Must give direct notice to interconnecting carriers | Always TRUE (federal). |
| 20 | `legacy_device_compatibility_check` | BOOLEAN | NO | Must verify compatibility with alarms, medical monitors, fax, etc. | Always TRUE (federal). |
| 21 | `local_row_permit_required` | BOOLEAN | NO | Local right-of-way / trenching permit required for fiber replacement dig | TRUE for ~70% of states (urban areas). |
| 22 | `historic_district_review` | BOOLEAN | NO | Additional review for work in historic districts | TRUE for ~30% of states. |
| 23 | `state_has_additional_requirements` | BOOLEAN | NO | State imposes requirements beyond federal baseline | TRUE for ~60% of states. |
| 24 | `additional_requirements_summary` | STRING | YES | Free-text summary of state-specific additional requirements | Synthetic realistic text: e.g., "Requires 12-month notice for rural exchanges with >50% elderly population" |
| 25 | `regulatory_contact_email` | STRING | YES | PUC contact email for copper retirement filings | Synthetic: `copper.retirement@puc.{state}.gov` |
| 26 | `last_updated_date` | DATE | NO | Last update date of this jurisdiction record | Random dates in 2025-06-01 to 2026-09-01 range |
| 27 | `effective_date` | DATE | NO | When these requirements became effective | 2026-03-26 for federal baseline (FCC 26-19 adoption date) |
| 28 | `notes` | STRING | YES | Additional notes | Synthetic text with state-specific context |

### State-Specific Variation Rules

To create realistic variation across states (not all identical):

- **Strict states** (CA, NY, MA, CT, IL, NJ, MD, WA): `puc_notice_days` 270-365, `residential_direct_notice_days` 120-180, `filing_type` = `application`, `backup_power_minimum_hours` = 24, `state_has_additional_requirements` = TRUE
- **Moderate states** (CO, MN, OR, PA, OH, MI, VA, GA, NC, WI, AZ): `puc_notice_days` 180-270, `residential_direct_notice_days` 90-120, `filing_type` = `tariff_amendment` or `informational_filing`
- **Light-touch states** (TX, FL, IN, ID, MT, WY, ND, SD, NE, KS, OK, AR, MS, AL, SC, TN, KY, WV, LA): `puc_notice_days` 150-180, `residential_direct_notice_days` 90, `filing_type` = `notification_only`
- **Deregulated states** (rare): `filing_type` = `no_state_filing`, minimal additional requirements
- **LEGACY_STATES** (CO, MN, WA, OR, ID, AZ): must be present and well-characterized since these are the demo's primary states

### FK Relationships
- No inbound FKs (this is a reference/lookup table)
- Outbound join: `state_code` → `tmf_shared.geographic_address.state_or_province` (after FIX-COORDINATES)
- Outbound join: `state_code` → `tmf_shared.geographic_site.state_province` (name mapping required)
- Feeds: P6-REG regulatory agent, P3-DLP `gold_regulatory_requirements_by_jurisdiction`, P4-SEQ optimizer constraints, P7-PLAN Gantt (notice-period scheduling)

---

## Table 2: `fcc_regulatory_document`

**Target catalog/schema:** `cdm_tmforum.copper_retirement` (or `cdm_tmforum.tmf_shared` if schema not created)
**Recommended row count:** 200 documents
**Determinism:** Follow `synthetic_assets.py` pattern.

### Column Specification

| # | Column | Type | Nullable | Description | Value Generation |
| --- | --- | --- | --- | --- | --- |
| 1 | `regulatory_document_id` | BIGINT | NO | PK, auto-increment from 60001 | Sequential |
| 2 | `document_id` | BIGINT | YES | FK to `tmf_shared.document` (optional — only for docs also registered there) | Sample from document.document_id where type='regulatory_filing' (381 available) |
| 3 | `docket_number` | STRING | NO | FCC/PUC docket number | Synthetic: `WC-{year}-{seq:03d}` for FCC, `PUC-{state}-{year}-{seq:03d}` for state |
| 4 | `document_type` | STRING | NO | Type of regulatory document | Categorical: `fcc_order`, `fcc_public_notice`, `fcc_guidance`, `state_puc_docket`, `state_puc_tariff`, `state_puc_ruling`, `carrier_section_214_filing`, `carrier_retirement_notice`, `state_governor_notice`, `compliance_checklist` |
| 5 | `title` | STRING | NO | Document title | Realistic synthetic: e.g., "In the Matter of Network and Services Modernization — Report and Order", "Notice of Copper Retirement — Wire Center DNVR-CO-001" |
| 6 | `issuing_body` | STRING | NO | Who issued the document | `Federal Communications Commission`, `{State} Public Utilities Commission`, `LakeLink Telecom` (carrier), etc. |
| 7 | `jurisdiction_state_code` | STRING | YES | State code if state-level document, NULL for federal | From state_puc_jurisdiction_requirements.state_code |
| 8 | `issued_date` | DATE | NO | Document publication date | Range: 2020-01-01 to 2026-09-01. FCC 26-19 docs cluster around 2026-03-26. |
| 9 | `effective_date` | DATE | YES | When the rule/order takes effect | issued_date + 30-90 days |
| 10 | `document_status` | STRING | NO | Status | Categorical: `final`, `proposed`, `interim`, `superseded`, `withdrawn` |
| 11 | `regulatory_topic` | STRING | NO | Primary topic | Categorical: `copper_retirement`, `section_214_discontinuance`, `network_change_disclosure`, `consumer_protection`, `911_coordination`, `backup_power`, `tribal_notice`, `right_of_way`, `tariff_amendment`, `broadband_transition` |
| 12 | `summary_text` | STRING | NO | 2-5 sentence summary of the document (synthetic but domain-realistic) | Generated per document_type + regulatory_topic. Key: must reflect corrected FCC 26-19 facts. |
| 13 | `full_text_excerpt` | STRING | YES | 1-3 paragraph excerpt for RAG retrieval grounding | Synthetic regulatory prose. Include real regulatory language patterns: "ORDERED", "NOTICE IS HEREBY GIVEN", "pursuant to Section 214(a)", etc. |
| 14 | `citation_reference` | STRING | YES | Legal citation | e.g., "47 U.S.C. § 214(a)", "47 C.F.R. § 63.71", "{State} Rev. Stat. § {section}" |
| 15 | `related_docket_numbers` | STRING | YES | Comma-separated related docket numbers | e.g., "WC-25-208, WC-25-209" |
| 16 | `wire_center_references` | STRING | YES | Wire center codes mentioned (if carrier filing) | Synthetic wire center codes from SPEC_wire_center_boundary |
| 17 | `carrier_name` | STRING | YES | Filing carrier (for carrier documents) | "LakeLink Telecom" (our synthetic carrier), NULL for government docs |
| 18 | `notice_period_days` | INT | YES | Notice period specified in this document | 90, 180, or state-specific |
| 19 | `file_format` | STRING | NO | Document format | Categorical: `pdf`, `txt`, `html` |
| 20 | `storage_uri` | STRING | YES | URI to full document in UC Volume | `/Volumes/cdm_tmforum/copper_retirement/regulatory_docs/{filename}` |
| 21 | `word_count` | INT | YES | Approximate word count | Range 500-15000 based on document_type |
| 22 | `page_count` | INT | YES | Approximate page count | word_count / 300 |
| 23 | `is_synthetic` | BOOLEAN | NO | Synthetic data label (always TRUE) | TRUE |
| 24 | `created_timestamp` | TIMESTAMP | NO | Record creation timestamp | Fixed synthetic timestamp |

### Document Type Distribution (200 documents)

| document_type | Count | Notes |
| --- | --- | --- |
| `fcc_order` | 15 | Major FCC orders including FCC 26-19, Tech Transitions Order (2015), prior copper retirement orders |
| `fcc_public_notice` | 20 | Public notices re: copper retirement proceedings |
| `fcc_guidance` | 10 | "What Government Officials Need to Know" style guidance docs |
| `state_puc_docket` | 50 | 1-2 per LEGACY_STATE + sampling across other states |
| `state_puc_tariff` | 20 | Tariff amendment filings |
| `state_puc_ruling` | 15 | PUC decisions on copper retirement petitions |
| `carrier_section_214_filing` | 30 | LakeLink Telecom Section 214 filings per wire center |
| `carrier_retirement_notice` | 25 | Copper retirement notices per wire center / exchange |
| `state_governor_notice` | 10 | 180-day advance notices to governors |
| `compliance_checklist` | 5 | Internal compliance checklists |

### Summary Text Templates (corrected FCC 26-19 grounding)

The generator MUST embed these corrected facts in `summary_text` and `full_text_excerpt`:

1. **For FCC 26-19 order docs:** "The FCC's Network and Services Modernization Order (FCC 26-19), adopted March 26, 2026, eliminated the Section 251(c)(5) network-change disclosure filing requirement for copper retirement. Section 214(a) discontinuance authorization remains required but is streamlined with 31-day automatic grants and consolidated tech-transition rules."
2. **For Section 214 filings:** "Pursuant to Section 214(a) of the Communications Act, [carrier] hereby seeks authorization to discontinue [service] in [wire_center]. Under FCC 26-19 streamlining, this application is subject to 31-day automatic grant unless the Commission acts to extend review."
3. **For state notices:** "In accordance with federal requirements and [State] PUC regulations, [carrier] provides [N]-day advance notice of planned copper network retirement in [wire_center/exchange]. Direct written notice to [count] affected residential customers will be delivered no later than [date]."
4. **NEVER generate text claiming Section 214 was eliminated** — this is the #1 misconception to avoid per BUILD-PLAN.md §0.

### FK Relationships
- `document_id` → `tmf_shared.document.document_id` (optional — 381 `regulatory_filing` type docs available)
- `jurisdiction_state_code` → `state_puc_jurisdiction_requirements.state_code`
- `wire_center_references` → synthetic wire center codes from SPEC_wire_center_boundary
- Feeds: P6-REG regulatory RAG agent (primary corpus), P1-REG bronze ingestion, P3-DLP silver document enrichment

---

## Companion Files: UC Volume Regulatory Document Corpus

**Target Volume:** `/Volumes/cdm_tmforum/copper_retirement/regulatory_docs/`
**File count:** 50-100 text files (subset of the 200 documents)
**Format:** `.txt` files with structured regulatory prose

### File Naming Convention
- FCC orders: `FCC_{docket_number}_{title_slug}.txt`
- State PUC: `PUC_{state_code}_{docket_number}_{title_slug}.txt`
- Carrier filings: `S214_{carrier}_{wire_center}_{date}.txt`
- Notices: `NOTICE_{type}_{state}_{date}.txt`

### Content Pattern (matches `bronze_contract_pdfs` Auto Loader architecture)
Each file should be 500-5000 words of synthetic but realistic regulatory text, structured with:
- Header (docket number, parties, date)
- Preamble / background
- Operative section (ORDERED / RESOLVED / NOTICE IS HEREBY GIVEN)
- Signature block

These files will be ingested via the same Auto Loader pattern as `revenue_assurance.bronze_contract_pdfs` (one row per file) and then parsed via `ai_parse_document` (same pattern as `silver_doc_intelligence_contracts`).

---

## Blockers & Dependencies

1. **Schema creation:** `copper_retirement` schema may not exist yet in `cdm_tmforum`. Generator should CREATE SCHEMA IF NOT EXISTS or place tables in `tmf_enterprise` / `tmf_shared` as fallback.
2. **Wire center codes:** `wire_center_references` column depends on SPEC_wire_center_boundary wire center naming convention. Use placeholder format `{STATE}-{SEQ:03d}` (e.g., `CO-001`, `MN-042`) consistent with that spec.
3. **UC Volume creation:** `/Volumes/cdm_tmforum/copper_retirement/regulatory_docs/` must be created before writing files. Check if volume exists; create if not.
4. **No FIX-COORDINATES dependency:** Unlike geo-spatial specs, this table does not depend on coordinate fixes. Can be executed independently.
5. **Regulator FK (optional):** Could create synthetic FCC + state PUC entries in `tmf_enterprise.regulator` (IDs 11001-11056) to link, but this modifies an existing TMF table. Recommend a standalone `regulator_id` column in `state_puc_jurisdiction_requirements` instead. Decision deferred to @pm.

---

## Implementation Notes

- **Seed:** Use `random.Random(42)` for reproducibility (consistent with other SPEC generators).
- **No scheduled-run DML:** Like FIX-COORDINATES, the generator notebook cannot run DML in scheduled agent runs. Implementation will be a separate notebook for manual or job execution.
- **LEGACY_STATES priority:** Ensure CO, MN, WA, OR, ID, AZ have the most detailed and realistic jurisdiction entries and the most documents (these are the demo's primary states).
- **Synthetic provenance:** All generated text must include `[SYNTHETIC]` markers or `is_synthetic=TRUE` column to comply with the project's "clearly labeled synthetic" rule (BUILD-PLAN.md §1).
