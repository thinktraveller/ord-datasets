# ord-datasets

This repository is the publication workspace for processed Open Reaction
Database datasets, their reproducible processing pipeline, intermediate
artifacts, and provenance records.

The project is currently at **build step 01 (scaffold only)**. No dataset has
been copied or published yet. The authoritative scope and implementation plan
are documented in:

- `project-docs/goal.md`
- `project-docs/project-plan.md`
- `project-docs/buildlog.md`

## Source boundaries

The sibling directories `../ord-data/` and `../dataset/` are read-only inputs.
Build commands must write only inside this repository. Original ORD Parquet
files are referenced by immutable source metadata and are not copied here.
Remote uploads require the explicit release gate defined in the project plan.

## Planned areas

- `datasets/`: complete corpus datasets and target-specific model-ready views.
- `intermediate/`: versioned artifacts for each processing stage.
- `pipeline/`: scripts, tests, policies, schemas, configurations, and workflows.
- `provenance/`: source, dataset, transformation, artifact, and row lineage.
- `reports/`: data-quality, licensing, and release-acceptance evidence.

All directories created in step 01 are placeholders for later validated steps.
