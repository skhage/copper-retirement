# Regulatory Compliance

## Overview

The Regulatory Compliance domain tracks the legal and regulatory requirements governing Lakelink Fiber's copper retirement — answering "what filings are needed, what notice periods apply, and which wire centers require PUC or FCC authorization before discontinuance." This domain powers Beat 4 (Clear on Regs?) of the demo, combining structured jurisdiction data with a RAG-based regulatory assistant backed by Vector Search over 528 indexed regulatory documents.

## Key Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.state_puc_jurisdiction_requirements` | Reference | One row per state × requirement_type | 56 | State PUC jurisdiction requirements — filing types, notice periods, governor notification rules per state. |
| `copper_retirement.fcc_regulatory_document` | Reference | One row per FCC document | 305 | FCC regulatory documents — Section 214, copper retirement orders, broadband transition rulings. |
| `copper_retirement.fcc_bdc_provider_coverage` | Reference | One row per provider × coverage_area | 7,223 | FCC Broadband Data Collection provider coverage — who serves what areas at what speeds. |
| `copper_retirement.fcc_fabric_location` | Reference | One row per fabric location | 10,000 | FCC Broadband Serviceable Location Fabric — eligible locations for broadband service. |
| `copper_retirement.regulatory_doc_chunks` | Reference | One row per document chunk | 528 | Chunked regulatory documents for Vector Search RAG — embeddings via GTE-large model. |
| `copper_retirement.regulatory_doc_chunks_vs_index` | Foreign (VS) | Vector Search index | 528 | Vector Search index over regulatory doc chunks — ONLINE on `demo_telco_vs_endpoint`. |
| `copper_retirement.reg_rag_eval_dataset` | Reference | One row per eval question | 35 | Evaluation dataset for the regulatory RAG assistant — questions with expected answers. |
| `copper_retirement.dig_safe_incident` | Reference | One row per incident | 5,000 | Dig-safe / one-call incidents — underground utility damage events relevant to construction planning. |
| `copper_retirement.bronze_dig_safe_incidents` | Bronze (MV) | One row per incident | 5,000 | DLP-materialized dig-safe incidents with standardized fields. |

### TMF Source Tables

| Table | Rows | Description |
|---|---|---|
| `tmf_enterprise.regulator` | 1,000 | Regulatory bodies — PUCs, FCC, state commissions with jurisdiction metadata. |
| `tmf_shared.document` | 10,000 | Document repository — regulatory filings, compliance certificates, policy documents. |
| `tmf_marketsales.policy` | 10,000 | Regulatory and business policies — structured rules governing copper retirement. |
| `tmf_marketsales.policy_rule` | 100,000 | Policy rules — executable conditions and actions derived from regulatory policies. |

## Entity Relationships

```
state_puc_jurisdiction_requirements
  └── jurisdiction_state_code → copper_plant_wire_center_jurisdiction.state_code
  └── jurisdiction_state_code → gold_wire_center_scorecard.state_code

gold_wire_center_scorecard
  └── puc_filing_required (boolean) → derived from state_puc_jurisdiction_requirements
  └── section_214_required (boolean) → FCC requirement flag
  └── governor_notice_days → from state_puc_jurisdiction_requirements
  └── puc_notice_days → from state_puc_jurisdiction_requirements
  └── residential_direct_notice_days → FCC/state hybrid requirement

fcc_bdc_provider_coverage
  └── location_id → fcc_fabric_location.location_id

regulatory_doc_chunks
  └── (indexed into) → regulatory_doc_chunks_vs_index (Vector Search)

dig_safe_incident
  └── geographic_address_id → tmf_shared.geographic_address.geographic_address_id
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| PUC Filing Required | Count of wire centers requiring state PUC filing before retirement | `gold_wire_center_scorecard` WHERE puc_filing_required = TRUE |
| Section 214 Required | Count of wire centers requiring FCC Section 214 discontinuance authorization | `gold_wire_center_scorecard` WHERE section_214_required = TRUE |
| Max Notice Period | Longest notice period across all jurisdictions for a wire center | MAX(governor_notice_days, puc_notice_days, residential_direct_notice_days) |
| Regulatory Docs Indexed | Total documents available for RAG assistant queries | `regulatory_doc_chunks` COUNT |
| Dig-Safe Incident Rate | Incidents per construction zone per month | `dig_safe_incident` GROUP BY area, month |

## Data Quality Notes

- **Jurisdiction data:** 56 state PUC requirement records covering all 6 LEGACY states with specific filing types, notice periods, and governor notification rules.
- **FCC documents:** 305 regulatory documents. 528 chunks indexed in Vector Search (GTE-large embeddings, ONLINE status).
- **FCC coverage:** 7,223 provider coverage records + 10K fabric locations for broadband availability analysis.
- **RAG evaluation:** 35-question eval dataset for regulatory assistant quality testing.
- **Dig-safe:** 5,000 incidents, materialized through DLP pipeline as `bronze_dig_safe_incidents`.
- **Vector Search:** Index `regulatory_doc_vs_index` is ONLINE on `demo_telco_vs_endpoint`. Queries via the regulatory assistant app.

## Related Domains

- **Physical Plant** — Wire center PUC jurisdiction requirements determine filing deadlines
- **Financial Operations** — PUC filing timelines constrain retirement milestone scheduling
- **Customer Impact** — Customer notification requirements depend on state PUC rules
- **Circuits & Services** — FCC broadband coverage data validates alternative service availability
