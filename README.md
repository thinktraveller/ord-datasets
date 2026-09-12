# ord-datasets model-ready preview

`v0.1.0-model-ready-preview-1` is a local, model-ready-only preview release candidate. It contains 19 target packages from 15 packages: 190 payload files totaling 211008093 bytes.

It is not a complete ORD corpus release and not an accepted benchmark. The 41 corpus payloads, all original ORD Parquet payloads, and all `_needs_review` payloads are explicitly excluded. Corpus identities in lineage are reference-only and are not downloadable payloads.

Every target includes its dataset, schema, configuration, row map, audit, exclusions, immutable source links, build provenance, metadata, and checksums. Verify the release with `provenance/model-ready-preview/release-manifest.json`, `provenance/model-ready-preview/artifact-inventory.csv`, and each target's `checksums.csv`.

## Readiness status

The statuses below are preserved from staging and do not imply benchmark acceptance:

- `active_generated_pending_release_validation`: 7
- `generated_adapter_blocked`: 1
- `generated_pending_campaign_evaluation`: 6
- `generated_with_source_caveat`: 1
- `partial_scope_generated`: 1
- `research_only_benchmark_blocked`: 3
