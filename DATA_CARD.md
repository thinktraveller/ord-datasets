# Model-ready preview data card

This release candidate packages task-specific projections derived from ORD, rather than a complete reaction corpus. Each target retains the source-defined label type and unit, included/excluded decisions, audit trail, and two-hop lineage through a reference-only logical corpus identity to a revision-pinned ORD source file.

Data and data-derived metadata are offered under CC BY-SA 4.0. The accompanying build and validation code is Apache-2.0. See `NOTICE`, `LICENSE-DATA`, and `LICENSE-CODE`. The original ORD Parquet files are not redistributed here; `source-links.json` and `provenance/source-files.initial.csv` provide immutable source identities, hashes, LFS OIDs, and commit-pinned URLs.

Known target readiness statuses are retained verbatim in `datasets/catalog.csv` and each `metadata.json`. In particular, partial, research-only, source-caveat, adapter-blocked, and campaign-evaluation-pending targets must not be presented as accepted benchmarks.
