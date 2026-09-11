# Model-ready target semantic-name and status review

## Result

The target map contains 19 targets from 15 packages.
Every target has a unique semantic slug, source logical/physical set, standardized schema hash,
label field/type/unit, included/excluded counts, artifact status and independent readiness status.

## Status contract

An artifact status of generated only confirms that its target files exist. It does not assert a complete
benchmark or campaign result. Readiness status preserves partial scope and source/domain/adapter blockers.
The full target map therefore exposes target files without promoting a blocked package to accepted status.

## Validation

- packages: 15; targets: 19; slug collisions: 0
- artifact status: {"generated": 19}
- readiness status: {"active_generated_pending_release_validation": 7, "generated_adapter_blocked": 1, "generated_pending_campaign_evaluation": 6, "generated_with_source_caveat": 1, "partial_scope_generated": 1, "research_only_benchmark_blocked": 3}
- label types: {"conversion_percent": 3, "hplc_response_percent": 3, "lc_uv_area_percent": 1, "reaction_yield_percent": 10, "relative_lc_area_ratio": 1, "signed_enantiomeric_excess_s_minus_r_percent": 1}

No target directory or data payload is created by this naming step. The complete semantic mapping is in
provenance/semantic-target-map.csv.
