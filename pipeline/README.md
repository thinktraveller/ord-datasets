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
