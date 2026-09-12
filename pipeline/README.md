# Processing pipeline

The pipeline builds corpus and model-ready staging packages, records
content-addressed intermediate/provenance indexes, and validates a release
candidate. It accepts explicit roots; it never writes into a source root.

Install the pinned tool environment from this directory:

```bash
uv sync --group dev
uv run pytest
uv run ruff check scripts tests
```

The build scripts require explicit source and output arguments. The main
release checks run from the repository root, for example:

```bash
uv --directory pipeline run python ../pipeline/scripts/validate_release_contracts.py
```

`archive_intermediate_indices.py`, `archive_model_ready_intermediates.py`, and
`audit_needs_review.py` create hash indexes only. They intentionally do not
copy legacy raw payloads into regular Git or promote a quarantined object.

## Public-source clean-room sample

`rebuild_clean_room_sample.py` resolves a revision-pinned Git LFS pointer via
the public Git LFS batch protocol, verifies the downloaded Parquet hash, then
builds a physical CSV, logical corpus, the frozen Ahneman standardized yield
target projection, and provenance under an empty output root. It deliberately
has no local source/staging/cache input option. Keep the transient
`--download-root` outside this repository; the Parquet source itself is never
promoted into the repository.

The extracted target contract fixes the feature columns, RDKit canonical-SMILES
selection, unique desired/single-product structured percentage-YIELD policy,
temperature/time unit conversion, source reaction-key policy, row ordering,
and CSV serialization. Other targets fail closed until their own frozen
contract has been extracted.

From the repository root, a representative invocation is:

```bash
clean_download_root="$(mktemp -d)"
clean_output_root="$(pwd)/.staging/clean-room-ahneman"

uv --directory pipeline run python ../pipeline/scripts/rebuild_clean_room_sample.py \
  --source-manifest "$(pwd)/provenance/source-files.initial.csv" \
  --semantic-map "$(pwd)/provenance/semantic-name-map.csv" \
  --members "$(pwd)/provenance/logical-dataset-members.csv" \
  --target-map "$(pwd)/provenance/semantic-target-map.csv" \
  --schema-dir "$(pwd)/pipeline/schemas" \
  --physical-id ord_dataset-46ff9a32d9e04016b9380b1b1ef949c3 \
  --target-id ahneman_yield_percent \
  --download-root "$clean_download_root" \
  --output-root "$clean_output_root" \
  --report-path "$(pwd)/reports/release-acceptance/step-20-clean-room-rebuild.json"
```

Supply the optional baseline manifests and physical archive index to enforce
the committed byte/semantic comparison. Run a second invocation with a fresh
download/output root and `--expected-output-root-sha256` set to the first
report's output-root hash. The step-20 report names any remaining
target-contract mismatch explicitly; it is not a release acceptance override.
