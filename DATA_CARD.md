# ord-datasets data card

This local draft has two distinct contracts. `datasets/corpus/` is the
complete, redacted ORD corpus: 41 semantic logical datasets, 53 physical
sources and 2,428,291 reactions. `datasets/model-ready/` is a task-specific
projection: 19 targets across 15 packages, with 128,712 included and 499
excluded source decisions. A reaction can appear in more than one target;
target counts never replace the corpus count.

Data-derived artifacts are CC BY-SA 4.0; pipeline code is Apache-2.0. See
`NOTICE`, `LICENSE-DATA`, `LICENSE-CODE`, and `provenance/license-inventory.csv`.
The corpus staging process removes literal email values from reaction JSON.

Every final row is intended to resolve in two hops: its corpus lineage fields
or target row map select `source-links.json`, then
`provenance/source-files.csv` supplies an ORD revision-pinned source URL and
SHA-256. `provenance/row-lineage/` contains compact indexes and examples.

This is not a published benchmark. Some targets retain generated, partial, or
blocked readiness states in `datasets/catalog.csv`; `_needs_review` payload has
no first-release inclusion. The draft is blocked on a dependency lock, an
externally verified storage pilot, clean-room source download, and explicit
publication authorization.
