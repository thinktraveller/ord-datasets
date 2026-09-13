# Published dataset views

This area has two separate data contracts:

- `corpus/` catalogs 41 semantically named logical datasets covering all 53
  physical ORD datasets and all 2,428,291 reactions. Its large payload is
  published separately on Hugging Face.
- `model-ready/` contains 19 target-specific views from 15 packages, with
  explicit labels, features, included/excluded rows, schemas, configurations,
  audit records, and release status. These files are a byte-for-byte copy of
  the immutable `v0.1.0-model-ready-preview-1` release, placed on `main` to make
  individual datasets and files easy to browse and download.

The separation is logical. Catalogs and content hashes reference shared
underlying objects where appropriate. Use the immutable release tag for a
version-pinned citation.
