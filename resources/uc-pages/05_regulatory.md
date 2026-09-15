# Regulatory Domain

**Schema:** `cdm_tmforum.copper_retirement`

## Overview

FCC broadband data, serviceable location fabric, regulatory documents, vector search indexes, and state PUC jurisdiction requirements.

## Tables (8)

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
* state_code links PUC requirements -> state-level aggregations

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

Key columns: provider_id, provider_name, location_id, technology_code, max_download_speed, max_upload_speed, state_code, county_fips

### `fcc_fabric_location` (Managed)

> Synthetic FCC Broadband Serviceable Location (BSL) Fabric -- aligned with tmf_shared_geography.

Key columns: location_id, address, latitude, longitude, state_code, county_fips, census_block, bsl_flag, h3_index

### `state_puc_jurisdiction_requirements` (Managed)

> Reference table of state PUC regulatory requirements for copper retirement -- notification periods, hearing requirements, service obligations.

Key columns: state_code, state_name, notification_period_days, public_hearing_required, service_obligation_type, alternative_service_requirement, regulatory_body

### `regulatory_doc_chunks` (Managed)

> FCC regulatory document chunks for Vector Search embeddings.

Key columns: chunk_id, document_id, chunk_text, chunk_index, document_title, document_type

### `reg_rag_eval_dataset` (Managed)

> Regulatory RAG evaluation dataset for Beat 4 copper retirement. 35 Q&A pairs covering regulatory compliance topics.

Key columns: question_id, question, expected_answer, topic, difficulty, source_document
