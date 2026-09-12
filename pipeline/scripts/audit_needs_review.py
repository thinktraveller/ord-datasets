#!/usr/bin/env python3
"""Audit every legacy ``_needs_review`` object without copying its payload."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


HEADER = [
    "artifact_id", "old_path", "size_bytes", "sha256", "review_disposition",
    "canonical_artifact_id", "canonical_old_path", "dedup_relation", "license_id",
    "redistribution_status", "release_inclusion", "reason",
]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def build(inventory_path: Path, output_path: Path, report_path: Path) -> dict[str, object]:
    with inventory_path.open(encoding="utf-8", newline="") as handle:
        inventory = list(csv.DictReader(handle))
    by_id = {row["artifact_id"]: row for row in inventory}
    rows = [row for row in inventory if row["object_type"] != "dir" and row["old_path"].startswith("processing/_needs_review/")]
    if len(rows) != 210:
        raise ValueError(f"expected 210 review files, found {len(rows)}")
    if output_path.exists() or report_path.exists():
        raise FileExistsError("refusing to overwrite an existing review audit")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    deduplicated = 0
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, lineterminator="\n")
        writer.writeheader()
        for row in sorted(rows, key=lambda item: item["old_path"]):
            canonical = by_id.get(row["canonical_artifact_id"])
            external_canonical = canonical is not None and not canonical["old_path"].startswith("processing/_needs_review/")
            if external_canonical:
                disposition = "superseded"
                inclusion = "excluded_duplicate"
                relation = "byte_identical_to_non_review_canonical"
                reason = "Legacy duplicate is excluded; the separately classified canonical object is referenced by SHA-256."
                deduplicated += 1
            else:
                disposition = "quarantined"
                inclusion = "not_in_initial_release"
                relation = "no_approved_external_canonical"
                reason = "License, sensitivity, relevance and reproducibility review is incomplete; payload remains quarantined."
            counts[disposition] += 1
            writer.writerow({
                "artifact_id": row["artifact_id"], "old_path": row["old_path"],
                "size_bytes": row["size_bytes"], "sha256": row["sha256"],
                "review_disposition": disposition, "canonical_artifact_id": row["canonical_artifact_id"],
                "canonical_old_path": "" if canonical is None else canonical["old_path"],
                "dedup_relation": relation, "license_id": row["license_candidate_id"],
                "redistribution_status": row["redistribution_status"], "release_inclusion": inclusion,
                "reason": reason,
            })
    report = {
        "schema_version": "1.0.0", "step_id": "step-18", "status": "complete",
        "input_inventory_sha256": digest(inventory_path), "review_file_count": len(rows),
        "review_bytes": sum(int(row["size_bytes"]) for row in rows),
        "dispositions": dict(sorted(counts.items())), "deduplicated_aliases": deduplicated,
        "initial_release_included_payloads": 0,
        "rule": "Objects without an approved non-review canonical artifact remain quarantined; no review payload is copied into this repository.",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.artifact_inventory, args.output, args.report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
