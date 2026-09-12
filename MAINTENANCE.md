# Maintenance runbook

The initial release is not closed. This runbook governs the local draft until
the owner resolves the blocking backlog in `project-docs/release-backlog.md`.

For an ORD update, first freeze a new public upstream revision and recompute all
53 source hashes. Any changed source requires a new semantic version, a new
source manifest, regenerated corpus/model-ready staging, lineage graph and root
hash. Never overwrite an existing release tag or its object revision.

The schema family, naming policy, target policy, and release manifest versions
are compatibility contracts. Additive fields require an explicit minor-version
compatibility statement; changed meanings, removed fields, changed slugs, or
lineage-breaking behavior require a major version. Preserve aliases for renamed
display labels and never reuse a released artifact path for different bytes.

Each release repeats the dependency lock, clean-room source rebuild, storage
pilot/readback, local RC validation, owner go decision, immutable upload, and
remote no-cache readback. `_needs_review` stays excluded unless a documented
review changes its file-level disposition and license/sensitivity gate.
