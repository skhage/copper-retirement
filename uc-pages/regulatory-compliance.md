# Regulatory Compliance

## Overview

The Regulatory Compliance domain captures the federal and state regulatory landscape governing Lakelink Fiber's copper retirement program. It spans FCC Section 214 discontinuance rules, state Public Utility Commission (PUC) notice requirements across 56 jurisdictions, broadband coverage obligations from the FCC Broadband Data Collection (BDC), and a Vector Search-powered RAG corpus for the regulatory assistant chatbot (Beat 4). This domain ensures every retirement action meets jurisdictional notice periods, filing requirements, and consumer protection mandates.

## Key Tables

### Regulatory Reference Tables

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.state_puc_jurisdiction_requirements` | Reference | One row per state jurisdiction | 56 | State PUC regulatory requirements — notice periods (governor, PUC, residential, tribal), filing types (Section 214, Section 251(c)(5)), backup power disclosure, public notice rules. 28 columns covering all compliance dimensions. |
| `copper_retirement.fcc_regulatory_document` | Reference | One row per regulatory document | 305 | FCC and state PUC regulatory documents governing copper retirement proceedings — Section 214, notice requirements, backup power, E911 compliance. 24 columns with docket numbers, jurisdiction, effective dates. |

### Vector Search Corpus

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.regulatory_doc_chunks` | Bronze | One row per document chunk | 528 | FCC regulatory document chunks for Vector Search embedding. Each chunk links back to its parent document via `regulatory_document_id`. 19 columns including chunk text, metadata, and jurisdiction tags. |

### FCC Broadband Data

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.fcc_fabric_location` | Reference | One row per broadband serviceable location (BSL) | 10,000 | Synthetic FCC Broadband Serviceable Location Fabric — aligned with `tmf_shared.geographic_address`. Each row represents one BSL with latitude, longitude, H3 index, and address components. |
| `copper_retirement.fcc_bdc_provider_coverage` | Reference | One row per provider-technology-location combination | 7,223 | FCC BDC provider coverage data — technology offerings at each BSL. Includes copper vs fiber flags, download/upload speeds, and latency. |

### Evaluation Data

| Table | Layer | Grain | Rows | Description |
|---|---|---|---|---|
| `copper_retirement.reg_rag_eval_dataset` | Evaluation | One row per Q&A pair | 35 | Regulatory RAG evaluation dataset for the Beat 4 regulatory assistant. 35 curated question-and-answer pairs covering FCC rules, state notice requirements, Section 214 procedures, and backup power compliance. |

## Vector Search Infrastructure

| Component | Details |
|---|---|
| **VS Endpoint** | `demo_telco_vs_endpoint` (status: ONLINE) |
| **Index** | `regulatory_doc_vs_index` — 528 documents indexed |
| **Embedding Model** | GTE-large |
| **Source Table** | `copper_retirement.regulatory_doc_chunks` |
| **Chunking Strategy** | Document-level chunks with metadata preservation (docket number, jurisdiction, document type) |

## Entity Relationships

```
state_puc_jurisdiction_requirements
  └── state_code → (join key to all geographic tables)
  └── Links to: bronze_copper_devices.state, gold_circuit_revenue_at_risk.state_code
  └── Drives: notice period calculations, PUC filing requirements per state

fcc_regulatory_document
  └── regulatory_document_id (PK) → regulatory_doc_chunks.regulatory_document_id
  └── jurisdiction_state_code → state_puc_jurisdiction_requirements.state_code
  └── document_type: FCC_order, PUC_ruling, notice_requirement, guidance

regulatory_doc_chunks
  └── chunk_id (PK)
  └── regulatory_document_id → fcc_regulatory_document.regulatory_document_id
  └── jurisdiction_state_code → state_puc_jurisdiction_requirements.state_code
  └── → Vector Search index (regulatory_doc_vs_index) for RAG retrieval

fcc_fabric_location
  └── location_id (PK) → fcc_bdc_provider_coverage.location_id
  └── h3_res8 (spatial join) → tmf_shared.geographic_address.h3_res8
  └── state → state_puc_jurisdiction_requirements.state_code

fcc_bdc_provider_coverage
  └── bdc_record_id (PK)
  └── location_id → fcc_fabric_location.location_id
  └── is_copper_service (flag) — identifies copper-served locations for retirement impact
  └── provider_id → external provider registry

reg_rag_eval_dataset
  └── eval_id (PK)
  └── states_covered — maps to state_puc_jurisdiction_requirements for validation
  └── source_tables — references regulatory tables used to answer each question
```

## Key Metrics

| Metric | Definition | Source |
|---|---|---|
| Jurisdictions Covered | Number of state PUC jurisdictions with documented requirements (target: 56) | `state_puc_jurisdiction_requirements` row count |
| Document Corpus Size | Total regulatory documents indexed for RAG retrieval | `fcc_regulatory_document` row count (305 docs) |
| Chunk Index Size | Document chunks in Vector Search index | `regulatory_doc_chunks` row count (528 chunks) |
| Section 214 Required States | States requiring FCC Section 214 discontinuance authorization | `state_puc_jurisdiction_requirements.section_214_required = TRUE` |
| Max Notice Period (days) | Longest required notice period across all jurisdictions | `MAX(residential_direct_notice_days)` from `state_puc_jurisdiction_requirements` |
| Copper-Served BSL Count | Broadband serviceable locations currently served by copper | `fcc_bdc_provider_coverage WHERE is_copper_service = TRUE` |
| RAG Eval Coverage | Number of curated Q&A pairs for regulatory assistant evaluation | `reg_rag_eval_dataset` row count (35 pairs) |

## Data Quality Notes

- **Jurisdiction coverage gap:** The PUC requirements table covers all 56 jurisdictions (50 states + 6 territories), but the document corpus only covers 25 of those 56 states. Western states (legacy states: CO, MN, WA, OR, ID, AZ) are well covered for the demo. 32 states in PUC table have no corresponding documents.
- **Document chunking:** 528 chunks from 305 documents yields ~1.7 chunks per document. Short documents remain as single chunks; longer orders are split with metadata preserved.
- **FCC BDC data is synthetic:** `fcc_fabric_location` and `fcc_bdc_provider_coverage` are synthetically generated to align with `tmf_shared.geographic_address`. Real FCC BDC data would be sourced from the FCC public filing system.
- **Eval dataset is hand-curated:** 35 Q&A pairs authored by @ml-engineer covering 5 categories (FCC rules, state PUC, notice procedures, Section 214, backup power). Used for RAG quality scoring, not training.
- **Refresh:** Reference tables are static (updated when new regulations are issued). Vector Search index syncs from `regulatory_doc_chunks` on demand.

## Related Domains

- **Physical Plant** — `state_code` links PUC requirements to wire center locations and copper device deployments for per-state retirement compliance
- **Circuits & Services** — E911 voice services require special regulatory treatment under FCC rules before retirement
- **Financial** — PUC filing requirements and notice periods affect retirement timeline and EBITDA forecast scheduling
- **Customers** — Residential direct notice requirements (from `state_puc_jurisdiction_requirements`) drive customer communication planning
