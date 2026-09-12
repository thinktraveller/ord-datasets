# Initial release backlog

| ID | Owner | Blocking work | Exit evidence |
|---|---|---|---|
| B1 | resolved | `pipeline/uv.lock` is generated; its locked environment ran tests and lint. | Step-19 report is `complete`; `uv sync --group dev --locked`, pytest and Ruff passed. |
| B2 | resolved | The Ahneman standardized target contract is reconstructed from public LFS input only. | Step-20 is `complete`: physical CSV, corpus, and target CSV all byte-match their frozen hashes; an independent public rebuild matches the output-root hash. |
| B3 | project-owner | Choose authorized object backend, account quota, remote URL and visibility; run a pilot. | Pilot upload/pull/readback hashes pass. |
| B4 | project-owner | Decide initial version/tag, `_needs_review` scope and partial/blocked target presentation. | `provenance/release-decision.json` is a go decision. |
| B5 | project-owner | Promote RC, run all blocking checks, upload immutable release, and perform no-cache readback. | Steps 26–30 have accepted/released reports and matching remote root hash. |
