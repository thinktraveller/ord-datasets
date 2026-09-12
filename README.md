# ord-datasets

This repository is the local, content-addressed release workspace for
processed Open Reaction Database datasets, their reproducible processing
pipeline, intermediate indexes, and provenance records. It has 41 validated
corpus staging packages and 19 validated model-ready target staging packages;
it has not been uploaded or released. The authoritative scope, build log, and
release gates are documented in:

- `project-docs/goal.md`
- `project-docs/project-plan.md`
- `project-docs/buildlog.md`

## Source boundaries

The sibling directories `../ord-data/` and `../dataset/` are read-only inputs.
Build commands must write only inside this repository. Original ORD Parquet
files are referenced by immutable source metadata and are not copied here.
Large staged data remains outside regular Git until an authorized external
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
