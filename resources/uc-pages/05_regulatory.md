# Regulatory Domain

**Schema:** `cdm_tmforum.copper_retirement`

## Overview

FCC broadband data, serviceable location fabric, regulatory documents, vector search indexes, and state PUC jurisdiction requirements.

## Tables (8)

> **Row/column counts:** fcc_bdc_provider_coverage (21 cols, 7,223 rows), fcc_fabric_location (20 cols, 10,000 rows), fcc_regulatory_document (24 cols, 305 rows), regulatory_doc_chunks (19 cols, 528 rows), state_puc_jurisdiction_requirements (28 cols, 56 rows), reg_rag_eval_dataset (11 cols, 35 rows). VS foreign tables are index-backed.

| Table | Type | Description |
|-------|------|-------------|
| `fcc_bdc_provider_coverage` | MANAGED | Synthetic FCC Broadband Data Collection (BDC) provider coverage |
| `fcc_fabric_location` | MANAGED | Synthetic FCC Broadband Serviceable Location (BSL) Fabric |
| `fcc_regulatory_document` | MANAGED | FCC regulatory document corpus |
| `regulatory_doc_chunks` | MANAGED | Copper retirement: FCC regulatory document chunks for Vector Search embeddings |
| `regulatory_doc_chunks_vs_index` | FOREIGN | Managed Vector Index with Delta Sync |
| `regulatory_doc_vs_index` | FOREIGN | Managed Vector Index with Delta Sync |
| `state_puc_jurisdiction_requirements` | MANAGED | Reference table of state PUC regulatory requirements for copper retirement |
| `reg_rag_eval_dataset` | MANAGED | Regulatory RAG evaluation dataset -- 35 Q&A pairs covering regulatory topics |

## Key Relationships

* location_id links fcc_fabric_location -> fcc_bdc_provider_coverage
* regulatory_doc_chunks feeds vector search indexes for RAG
* state_code / state links PUC requirements -> state-level aggregations (note: fcc tables use `state`, PUC table uses `state_code`)

## RAG Architecture

The regulatory domain implements a RAG (Retrieval-Augmented Generation) pipeline:

1. **Source**: `fcc_regulatory_document` contains full regulatory documents
2. **Chunking**: `regulatory_doc_chunks` splits documents into embedding-ready chunks
3. **Indexing**: Two Vector Search indexes (`regulatory_doc_chunks_vs_index`, `regulatory_doc_vs_index`) provide semantic search
4. **Serving**: The `regulatory-assistant` app uses these indexes for Q&A
5. **Evaluation**: `reg_rag_eval_dataset` contains 35 Q&A pairs for RAG quality testing

## Table Details

### `fcc_bdc_provider_coverage` (Managed)

> Synthetic FCC Broadband Data Collection (BDC) provider coverage. Each row = one provider's coverage at a location.

Key columns: bdc_record_id, provider_id, provider_name, location_id, technology_code, max_download_mbps, max_upload_mbps, state, is_copper_service, is_fiber_service, in_legacy_copper_territory

### `fcc_fabric_location` (Managed)

> Synthetic FCC Broadband Serviceable Location (BSL) Fabric -- aligned with tmf_shared_geography.

Key columns: location_id, address_primary, latitude, longitude, state, census_block_fips, is_broadband_serviceable, h3_res8, h3_res9, in_legacy_copper_territory

### `state_puc_jurisdiction_requirements` (Managed)

> Reference table of state PUC regulatory requirements for copper retirement -- notification periods, hearing requirements, service obligations.

Key columns: jurisdiction_id, state_code, state_name, puc_name, puc_short_name, governor_notice_days, puc_notice_days, residential_direct_notice_days, tribal_notice_days, public_notice_required, section_214_required, filing_type

### `regulatory_doc_chunks` (Managed)

> FCC regulatory document chunks for Vector Search embeddings.

Key columns: chunk_id, regulatory_document_id, embedding_text, chunk_index, title, document_type, issuing_body, regulatory_topic

### `reg_rag_eval_dataset` (Managed)

> Regulatory RAG evaluation dataset for Beat 4 copper retirement. 35 Q&A pairs covering regulatory compliance topics.

Key columns: eval_id, question, expected_response, category, difficulty, source_tables, states_covered
