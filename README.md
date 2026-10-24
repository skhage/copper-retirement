# copper-retirement
Help telcos use data to retire outdated services, reduce costs and gain one-time revenue

**Partners start here:** [PARTNER-PLAYBOOK.md](PARTNER-PLAYBOOK.md) covers the roadmap, the cited SOW phase template, ROI inputs, the discovery questionnaire, the demo script, deploy, recovery and run cost. The former DEMO-RUNBOOK, DEMO-ROLLBACK-RECOVERY, DEMO-ENV-FREEZE-CHECKLIST and demo_kpi_cheat_sheet docs were merged into it on 2026-10-24 and are superseded (scheduled for deletion).

## Synthetic source-data fixtures

`data/fixtures/synthetic/` contains deterministic, ingest-ready demo fixtures
for the simulated OSS/GIS copper footprint, circuit inventory, copper recovery,
and contractor registry. Every row carries source-system, dataset-version,
seed, and synthetic-data notice fields. `manifest.json` records row counts and
SHA-256 hashes so downstream ingestion can verify provenance and file integrity.

Regenerate the committed fixtures entirely offline from the repository root:

```bash
python -m scripts.generate_synthetic_sources
```

Use `--output`, `--asset-count`, `--contractor-count`, or `--seed` to create a
different deterministic fixture set. The GIS CSV retains all fields consumed
by `risk.scoring`, and `gis_assets.geojson` provides H3-derived serving-area
polygons for file-based GIS ingestion.
