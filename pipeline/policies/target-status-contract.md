# Model-ready target status contract

Every model-ready target exposes two separate status fields.

- `artifact_status` says whether the declared target files were generated.
- `readiness_status` says whether the package can support the claimed campaign
  or benchmark use. It must retain partial scope and declared source, domain or
  adapter blockers.

No tooling may infer `accepted`, `complete`, or benchmark-ready from a target
directory, a normalized CSV, or an artifact status alone. A target may be
published with a visible research-only or caveated readiness status only after
all license, PII, provenance, validation, storage and release gates pass.

Label semantics are also contractual: yield percent, conversion percent,
relative LC area ratio, HPLC response percent, LC/UV area percent and signed
S-minus-R enantiomeric excess must remain distinct in catalog fields, units,
filenames, documentation, evaluation and downstream model claims.
