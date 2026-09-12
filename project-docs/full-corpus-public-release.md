# Full corpus public-release contract

## Identity

| Field | Value |
|---|---|
| Hugging Face Dataset repo | `thinktraveller/ord-processed-reaction-corpus` |
| Display name | `ORD Processed Reaction Corpus` |
| Published version | [`v0.2.0-corpus-preview-1`](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1) |
| Visibility | public, verified |
| Transport | Hugging Face Dataset repository backed by Xet |
| Private verified source snapshot | `corpus-staging-step11-4a546010d1aad3ba` |
| Immutable commit | `260cde0feb414c75b2bf971d6f3a4dbbee7b2e95` |

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
4. Complete: the Dataset Card, licenses, NOTICE, citation, and public wording
   were reviewed before the owner authorized publication.
5. Complete: `provenance/full-corpus-release-decision.json` records the owner
   `go` decision and public write authorization.
6. Complete: the exact candidate was uploaded to the HF Dataset repo and
   frozen at annotated tag `v0.2.0-corpus-preview-1` (peeled commit
   `260cde0feb414c75b2bf971d6f3a4dbbee7b2e95`). A fresh download passed all
   205 SHA-256 checks and complete validation with zero blocking checks.

## Non-goals

The private Hugging Face Bucket is a verified backup/transport layer, not this
public release. It is not made public and its mutable prefixes are not used as
release versions. `_needs_review` stays out of scope until its own review and
release decision are complete.

## Publication result

The public Dataset contains the exact 224-file candidate tree plus Hub's
automatic `.gitattributes` control file. The fresh tagged readback verified the
205 payload checksums and candidate root SHA-256
`930a9111b6e9f7a85abdff2199c8e7637a08822782cf8ffc5081b93e563bc663`.
No original ORD Parquet, `_needs_review`, clean-room duplicate, or model-ready
payload was included in this corpus release.
