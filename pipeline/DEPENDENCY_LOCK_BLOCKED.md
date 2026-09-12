# Dependency lock blocker

Step 19 records the exact dependency constraints in `pyproject.toml`, but a
new `uv.lock` has not been generated. The package index request for `ruff`
failed during TLS connection on 2026-09-12, and `uv lock --offline` confirmed
that its local cache lacks a resolvable ruff distribution.

No dependency was substituted silently. The checked local Python environment
contains `jsonschema`, `pytest`, and `ruff`, so it can run the source and test
checks recorded in the step-19 report. Re-run `uv lock` from this directory in
a network-enabled environment before a release candidate is accepted.
