# Source and write boundaries

## Read-only inputs

- `../ord-data/`
- `../dataset/`
- legacy coordination documents outside this repository

No build step may edit, move, rename, delete, or commit inside these inputs.

## Writable scope

All generated files must be written under the `ord-datasets/` repository. Work
in progress belongs under the ignored `.staging/<release-id>/<step-id>/` tree
until the relevant validation gate passes.

## Prohibited implicit actions

- Do not copy original `ord-data/data/**/*.parquet` into this repository.
- Do not upload, create a remote release, purchase storage, or expose review
  artifacts without the release authorization step.
- Do not commit virtual environments, caches, credentials, local absolute path
  configuration, or unreviewed third-party material.
- Do not treat `intermediate/90-legacy-needs-review/` as authoritative data.

Every promoted artifact must have an inventory entry, license decision, hash,
source relationship, and completed validation record.
