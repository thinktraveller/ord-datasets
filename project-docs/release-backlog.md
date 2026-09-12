# Initial release backlog

| ID | Owner | Blocking work | Exit evidence |
|---|---|---|---|
| B1 | project-owner | Restore package-index connectivity and generate `pipeline/uv.lock`. | Lock is committed and pipeline tests run in the locked environment. |
| B2 | project-owner | Provide a verified direct public source download route and complete a clean-room physical→logical→target sample. | Step-20 report has matching source/staging hashes. |
| B3 | project-owner | Choose authorized object backend, account quota, remote URL and visibility; run a pilot. | Pilot upload/pull/readback hashes pass. |
| B4 | project-owner | Decide initial version/tag, `_needs_review` scope and partial/blocked target presentation. | `provenance/release-decision.json` is a go decision. |
| B5 | project-owner | Promote RC, run all blocking checks, upload immutable release, and perform no-cache readback. | Steps 26–30 have accepted/released reports and matching remote root hash. |
