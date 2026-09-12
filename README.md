# ord-datasets

## Published data

The first model-ready data preview is published as
[`v0.1.0-model-ready-preview-1`](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1).
It contains 19 model-ready targets across 15 packages.

- [Browse the published model-ready targets](https://github.com/thinktraveller/ord-datasets/tree/release/v0.1.0-model-ready-preview-1/datasets/model-ready)
- [Browse the immutable release tag](https://github.com/thinktraveller/ord-datasets/tree/v0.1.0-model-ready-preview-1)

Clone the published preview:

```bash
git clone --depth 1 --branch v0.1.0-model-ready-preview-1 \
  https://github.com/thinktraveller/ord-datasets.git
```

The `main` branch contains the processing pipeline, release documentation, and
acceptance evidence. The published payload is intentionally kept on the
immutable release tag and its matching release branch so its manifest root hash
remains reproducible. This preview is not a complete ORD corpus release, does
not include original ORD Parquet or `_needs_review` payload, and must not be
presented as an accepted benchmark.

This repository is the local, content-addressed release workspace for
processed Open Reaction Database datasets, their reproducible processing
pipeline, intermediate indexes, and provenance records. It has 41 validated
corpus staging packages and 19 validated model-ready target staging packages.
The model-ready preview above is published; the 41-corpus release remains a
separate, unpublished track. The authoritative scope, build log, and release
gates are documented in:

- `project-docs/goal.md`
- `project-docs/project-plan.md`
- `project-docs/buildlog.md`

## Source boundaries

The sibling directories `../ord-data/` and `../dataset/` are read-only inputs.
Build commands must write only inside this repository. Original ORD Parquet
files are referenced by immutable source metadata and are not copied here.
The published model-ready preview uses the immutable release tag above; the
larger corpus payload remains outside regular Git until a separately authorized
object backend passes its readback pilot. Remote uploads require the explicit
release gate defined in the project plan.

## Planned areas

- `datasets/`: catalog for complete corpus and target-specific model-ready views.
- `intermediate/`: content-addressed indexes for each processing stage.
- `pipeline/`: scripts, tests, policies, schemas, configurations, and workflows.
- `provenance/`: source, dataset, transformation, artifact, and row lineage.
- `reports/`: data-quality, licensing, and release-acceptance evidence.

See `DATA_CARD.md` for scope, licenses, lineage, readiness states, and release
blockers. Run local checks with `python3 -m unittest discover -s
pipeline/tests`; generate `pipeline/uv.lock` in a network-enabled environment
before accepting a release candidate.
