# Published dataset views

This area has two separate data contracts:

- `corpus/` catalogs 41 semantically named logical datasets covering all 53
  physical ORD datasets and all 2,428,291 reactions. Its large payload is
  published separately on Hugging Face.
- `model-ready/` contains 19 target-specific views from 15 packages, with
  explicit labels, features, included/excluded rows, schemas, configurations,
  audit records, and release status. The main table in each target is named
  `<target-slug>-dataset.csv` and retains the same bytes as the immutable
  `v0.1.0-model-ready-preview-1` release's `dataset.csv`; separate English
  `README.md` and Chinese `README-zh.md` files provide plain-language guides
  for browsing and downloading individual datasets.

For every model-ready target, `yonod-config.json` is the field-role and example
configuration used by [YONOD](https://github.com/thinktraveller/YONOD); it is
optional for manual analysis. `target-build-provenance.json` records the inputs,
rules, and hashes needed to reproduce or audit the target build, while
`checksums.csv` lists file paths, SHA-256 fingerprints, and sizes for checking a
download's integrity.

The separation is logical. Catalogs and content hashes reference shared
underlying objects where appropriate. Use the immutable release tag for a
version-pinned citation.
