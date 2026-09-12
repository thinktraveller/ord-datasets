---
license: cc-by-sa-4.0
task_categories:
  - other
tags:
  - chemistry
  - reaction-data
  - open-reaction-database
  - provenance
size_categories:
  - 1M<n<10M
---

# ORD Processed Reaction Corpus

`v0.2.0-corpus-preview-1` is a provenance-preserving, sanitized derivative
corpus built from the Open Reaction Database (ORD). It provides 41 logical
corpus packages, 2,428,291 reactions, and traceability to 53 immutable ORD
physical source records.

## Scope

Each corpus package contains `reactions.csv`, `schema.json`,
`source-links.json`, `checksums.csv`, and `metadata.json`. The corpus release
also includes a corpus-only catalog, source/corpus provenance, licenses,
attribution, `SHA256SUMS`, and an immutable release manifest.

This corpus release does **not** contain original ORD Parquet payload,
`_needs_review` payload, clean-room duplicates, credentials, or the separately
released model-ready target payload. The latter remains available as the
[`v0.1.0-model-ready-preview-1` GitHub prerelease](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1).

## Provenance and integrity

Every corpus row is linked through its package `source-links.json` to a fixed
ORD upstream revision, source path, SHA-256, and Git LFS object ID. The release
ships `SHA256SUMS`; verify a downloaded snapshot with:

```bash
sha256sum -c SHA256SUMS
```

The publication pipeline validates 41 corpus packages, 53 physical sources,
and 2,428,291 reactions. Literal email values are removed from the published
sanitized derivative.

## License and attribution

The data derivative is distributed under CC BY-SA 4.0. See `LICENSE-DATA`,
`NOTICE`, and `CITATION.cff` in the release for the complete terms and
attribution. Cite the ORD source as well as this versioned derivative release.

## Status

This is a corpus release, not a claim that every possible downstream target is
an accepted benchmark. Target-specific model-ready data has its own readiness
states and release cadence.
