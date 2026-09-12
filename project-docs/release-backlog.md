# Model-ready preview release backlog

本 backlog 只覆盖 `model-ready-preview`：19 个 target/15 个 package 与必要的 catalog、provenance 和文档。它不发布 41 个 corpus payload、原始 Parquet 或 `_needs_review` payload，也不关闭后续 full release 工作。

| ID | Owner | Blocking work | Exit evidence |
|---|---|---|---|
| B1 | resolved | `pipeline/uv.lock` is generated; its locked environment ran tests and lint. | Step-19 report is `complete`; `uv sync --group dev --locked`, pytest and Ruff passed. |
| B2 | resolved | The Ahneman standardized target contract is reconstructed from public LFS input only. | Step-20 is `complete`: physical CSV, corpus, and target CSV all byte-match their frozen hashes; an independent public rebuild matches the output-root hash. |
| B3 | resolved | Ordinary Git pilot was authorized against the public `thinktraveller/ord-datasets` repository. It covered the immutable preview manifest, complete Ahneman target (6,073,626 bytes), and complete Pfizer target (69,097,967 bytes, including the 54,055,777-byte warning-threshold file). | Pilot branch `pilot/v0.1.0-model-ready-preview-1` at `b224523…` passed a no-LFS clean-clone byte-for-byte readback; see `step-25-model-ready-preview-pilot.json`. |
| B4 | resolved | The owner authorized public ordinary Git transport, release tag `v0.1.0-model-ready-preview-1`, model-ready-only scope, and `_needs_review=none`. | `provenance/release-decision.json` records the `go` decision and final published release; corpus and Parquet remain excluded. |
| B5 | resolved | The immutable model-ready preview was published and cloned anew without a local artifact fallback. | Branch/tag target `7d52dd2…`, GitHub prerelease, and remote readback all match root `24246a51…935e6`; see steps 29–30 preview reports. |

## Deferred full release

| ID | Owner | Deferred work | Exit evidence |
|---|---|---|---|
| F1 | resolved for private transport pilot | Hugging Face Storage Bucket/Xet was selected and piloted for the 41-corpus staging payload (13,127,476,889 bytes); no sharding was required. | Private bucket snapshot `corpus-staging-step11-4a546010d1aad3ba` uploaded 205 files, then passed a fresh 205/205 SHA-256 readback; see steps 25 and 30 HF reports. This does not authorize a public corpus release. |
| F2 | project-owner | Build a distinct full-release RC and immutable version after corpus-specific validation. | 41 corpus / 2,428,291 Reaction / 53 physical-source checks and a distinct full root hash pass. |
