# Initial release backlog

| ID | Owner | Blocking work | Exit evidence |
|---|---|---|---|
| B1 | resolved | `pipeline/uv.lock` is generated; its locked environment ran tests and lint. | Step-19 report is `complete`; `uv sync --group dev --locked`, pytest and Ruff passed. |
| B2 | pipeline-maintainer | Reconstruct the frozen standardized target projection contract so its data artifact byte-matches the clean-room sample. | Step-20 target dataset SHA-256 matches its frozen staging manifest; physical CSV and corpus already match. |
| B3 | project-owner | Choose authorized object backend, account quota, remote URL and visibility; run a pilot. | Pilot upload/pull/readback hashes pass. |
| B4 | project-owner | Decide initial version/tag, `_needs_review` scope and partial/blocked target presentation. | `provenance/release-decision.json` is a go decision. |
| B5 | project-owner | Promote RC, run all blocking checks, upload immutable release, and perform no-cache readback. | Steps 26–30 have accepted/released reports and matching remote root hash. |
