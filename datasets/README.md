# Published dataset views

This area has two separate data contracts:

- `corpus/` will contain 41 semantically named logical datasets covering all
  53 physical ORD datasets and all 2,428,291 reactions.
- `model-ready/` will contain 19 target-specific views from 15 packages, with
  explicit labels, features, included/excluded rows, schemas, configurations,
  audit records, and release status.

The separation is logical and does not require duplicate storage. Catalogs and
content hashes will reference shared underlying objects where appropriate.

No data is present at build step 01.
