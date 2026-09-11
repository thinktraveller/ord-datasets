# Release-contract field dictionary

Contract version: `1.1.0` (the 1.0.0 core remains compatible). All paths below are repository-relative POSIX
paths. SHA-256 values are lowercase hexadecimal digests of exact bytes.

| Contract | Field | Meaning | Required / nullable |
|---|---|---|---|
| catalog record | `record_type` | `corpus` is a full logical reaction view; `model-ready` is a target-specific projection. | required / no |
| catalog record | `logical_dataset_id` | Stable logical grouping ID; never replaced by a directory slug. | required / no |
| catalog record | `physical_dataset_ids` | One or more ORD physical source IDs represented by the record. | required / no |
| catalog record | `target_id` | Stable target identifier. It is `null` for corpus records. | required / yes |
| catalog record | `release_path` | Intended published directory; must match the record layer. | required / no |
| dataset metadata | `source_links_path` | Link to the per-dataset immutable source-link document. | required / no |
| dataset metadata | `included_count`, `excluded_count` | Projection decision counts; both are `null` for corpus. | required / yes |
| source link | `source_file_url` | Public GitHub blob URL pinned to an exact 40-hex ORD revision. | required / no |
| source link | `source_sha256` | Byte hash of the original ORD Parquet; it is also the LFS OID for the frozen source set. | required / no |
| artifact record | `disposition` | Allowed lifecycle decision: promoted, staged, quarantined, superseded, excluded, or manifest-only. | required / no |
| artifact record | `redistribution_status` | Separate right-to-redistribute gate; no `allow` record bypasses license or sensitive-data validation. | required / no |
| row-map record | `csv_row_number` | One-based row in the target `dataset.csv`. | required / no |
| row-map record | `source_row_index` | Zero-based source row in the corpus/physical conversion. | required / no |
| model-ready row map | `campaign_id` | Optional stable campaign key; it is retained when the upstream target is campaign-scoped and is never used as a label feature. | optional / no |
| transformation record | `input_artifact_ids`, `output_artifact_ids` | Hash-addressable graph nodes used to reconstruct the processing DAG. | required / no |
| transformation record | `pipeline_commit`, `config_sha256` | Exact code revision and configuration that performed the transformation. | required / no |
| release manifest | `root_sha256` | Deterministically calculated release hash-tree root, never hand-edited. | required / no |
| release manifest | `source_manifest_path` | The frozen file-level provenance table from which all fixed source links resolve. | required / no |

`physical_dataset_id → logical_dataset_id → target_id` is represented
non-destructively: catalog and metadata keep the physical ID array; model-ready
records additionally name the target; source-link records bind each physical
ID to its hash and immutable URL. Included and excluded target decisions both
retain row-map-compatible keys.
