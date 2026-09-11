# P7-REG — Regulatory Assistant

**Demo Beat 4:** "Are we clear on regs everywhere we touch?"

A React/TypeScript Databricks App providing a UI surface for the P6-REG
regulatory RAG agent. Helps telco executives understand copper retirement
regulatory requirements across jurisdictions.

## Screens

1. **Ask** — Chat interface to P6-REG agent with inline citations
2. **Jurisdiction Map** — US state choropleth showing compliance status
3. **Checklist** — Per-state/wire-center compliance tracking
4. **Documents** — Browse regulatory document corpus with search

## Data Sources

| Source | Table | Status |
|---|---|---|
| Regulators | `cdm_tmforum.tmf_enterprise.regulator` (1K) | AVAILABLE |
| Policies | `cdm_tmforum.tmf_marketsales.policy` (10K) | AVAILABLE |
| Policy rules | `cdm_tmforum.tmf_marketsales.policy_rule` (100K) | AVAILABLE |
| Documents | `cdm_tmforum.tmf_shared.document` (10K) | AVAILABLE |
| Jurisdiction lookup | Synthetic (P0-DATAGEN-REG) | BLOCKED |
| Agent endpoint | P6-REG Model Serving | BLOCKED |
| FCC corpus | P1-REG document store | BLOCKED |

## Architecture

- **Framework:** AppKit (React/TypeScript)
- **Data access:** SQL warehouse (analytics plugin)
- **Agent integration:** SSE to P6-REG endpoint (when deployed)
- **Mock mode:** `USE_MOCK_DATA = true` — 15 pre-built Q&A pairs
  grounded in corrected FCC 26-19 facts from BUILD-PLAN.md §0

## Running

```bash
npm install
npm run dev
```

## Dependencies

Blocked on:
- P0-DATAGEN-REG (state PUC jurisdiction requirements)
- P6-REG (regulatory RAG agent endpoint)
- P1-REG (FCC document corpus)

All data is **SYNTHETIC**.
