# Model-ready preview release backlog

本 backlog 只覆盖 `model-ready-preview`：19 个 target/15 个 package 与必要的 catalog、provenance 和文档。它不发布 41 个 corpus payload、原始 Parquet 或 `_needs_review` payload，也不关闭后续 full release 工作。

| ID | Owner | Blocking work | Exit evidence |
|---|---|---|---|
| B1 | resolved | `pipeline/uv.lock` is generated; its locked environment ran tests and lint. | Step-19 report is `complete`; `uv sync --group dev --locked`, pytest and Ruff passed. |
| B2 | resolved | The Ahneman standardized target contract is reconstructed from public LFS input only. | Step-20 is `complete`: physical CSV, corpus, and target CSV all byte-match their frozen hashes; an independent public rebuild matches the output-root hash. |
| B3 | project-owner | Choose remote URL/owner/visibility and preview transport: ordinary Git is allowed for this 211,008,093-byte set (largest file 54,055,777 bytes, with >50 MiB warnings); LFS/object storage remains optional and needs quota. Authorize a limited pilot. | The selected transport pilot uploads/reads back a manifest, one complete target and the largest-file target with matching hashes; ordinary Git additionally passes a no-LFS clean clone. |
| B4 | project-owner | Freeze a preview version/tag, exact model-ready-only scope, `_needs_review=none`, target-status presentation and final remote-write authorization. | `provenance/release-decision.json` is a `go` decision for `model-ready-preview`; it explicitly says corpus/Parquet are excluded. |
| B5 | project-owner | Promote only the 19-target preview RC, run preview-specific checks, upload immutable release, and perform no-cache readback. | Steps 26–30 have preview acceptance/released reports and a matching preview root hash; no corpus payload or Parquet is present. |

## Deferred full release

| ID | Owner | Deferred work | Exit evidence |
|---|---|---|---|
| F1 | project-owner | Select and pilot a large-object backend for the 41-corpus payload (about 13.13 GB), including any required sharding and quota. | Full-release object pilot/readback passes. |
| F2 | project-owner | Build a distinct full-release RC and immutable version after corpus-specific validation. | 41 corpus / 2,428,291 Reaction / 53 physical-source checks and a distinct full root hash pass. |
