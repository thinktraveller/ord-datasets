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
  semantic-name-map.csv
  logical-dataset-members.csv
  corpus-only release manifest and lineage records
```

## Required gates

1. Build the candidate in a new ignored release root; refuse to overwrite an
   existing version.
2. Verify every corpus package against the frozen source/member/control
   manifests and the private bucket snapshot SHA256SUMS.
3. Validate the complete candidate's schema, license, redaction, scope,
   lineage, file count, byte count, and deterministic root hash.
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
