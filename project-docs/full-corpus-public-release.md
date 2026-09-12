# Full corpus public-release contract

## Identity

| Field | Value |
|---|---|
| Hugging Face Dataset repo | `thinktraveller/ord-processed-reaction-corpus` |
| Display name | `ORD Processed Reaction Corpus` |
| Proposed initial version | `v0.2.0-corpus-preview-1` |
| Visibility | public, pending final owner authorization |
| Transport | Hugging Face Dataset repository backed by Xet |
| Private verified source snapshot | `corpus-staging-step11-4a546010d1aad3ba` |

## Fixed scope

The public RC must contain exactly 41 sanitized corpus directories, 205 payload
files, 13,127,476,889 payload bytes, 53 referenced physical sources, and
2,428,291 reactions. It must contain a corpus-only catalog and all required
license, citation, provenance, checksum, and manifest files.

The RC must not contain original ORD Parquet, `_needs_review`, clean-room
duplicates, credentials, caches, local absolute paths, or model-ready target
payload. Model-ready data remains a distinct, already published preview release
with its own immutable tag and readiness language.

## Candidate tree

```text
README.md                         # rendered HF dataset card
LICENSE-DATA
LICENSE-CODE
NOTICE
CITATION.cff
SHA256SUMS
datasets/
  catalog.csv                     # 41 corpus records only
  catalog.json
  corpus/<package>/{reactions.csv,schema.json,source-links.json,checksums.csv,metadata.json}
provenance/
  source-files.csv
  source-files.initial.csv         # retained for per-package source-link contract compatibility
  semantic-name-map.csv
  logical-dataset-members.csv
  full-corpus-release/{private-transport-SHA256SUMS,staging-control-manifest.json,
                       artifact-inventory.csv,release-artifacts.jsonl,
                       lineage-edges.csv,transformations.jsonl,release-manifest.json}
```

## Required gates

1. Complete: the candidate was built atomically in ignored root
   `release-candidates/v0.2.0-corpus-preview-1`; it refuses to overwrite an
   existing version. Step-31 root SHA-256:
   `930a9111b6e9f7a85abdff2199c8e7637a08822782cf8ffc5081b93e563bc663`.
2. Complete: all 41 corpus packages were verified against frozen
   source/member/control manifests and private snapshot SHA256SUMS
   `4a546010d1aad3badc567a74be149afe53b21606cc518126d41e0b81d22a21af`.
3. Complete: independent local validation passed schema, license, redaction,
   scope, lineage, file count, byte count, and deterministic root hash with
   zero blocking checks. See steps 31–32 full-corpus reports.
4. Review the rendered Dataset Card, license, NOTICE, citation, and public
   wording. The repo must not imply ORD affiliation or an accepted benchmark.
5. Change `provenance/full-corpus-release-decision.json` to `go` only after the
   preceding gates pass and the owner explicitly authorizes the public HF
   repository write.
6. Upload the exact candidate to the HF Dataset repo, freeze an immutable
   revision/version, then run a clean remote readback and all-file SHA-256
   verification before declaring publication complete.

## Non-goals

The private Hugging Face Bucket is a verified backup/transport layer, not this
public release. It is not made public and its mutable prefixes are not used as
release versions. `_needs_review` stays out of scope until its own review and
release decision are complete.

## Local candidate status

The validated candidate is local and Git-ignored; its payload was not added to
the source repository and no public Hugging Face write was attempted. It is
ready only for the owner review and explicit public-write decision in gate 5.
