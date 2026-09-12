#!/usr/bin/env python3
"""Create immutable, payload-free archive indexes for intermediate stages.

The legacy workspace contains raw physical CSV and pre-redaction model assets.
Those files are intentionally not copied into the publication repository:
their SHA-256, source-relative path, disposition and replacement relation are
recorded here instead.  This preserves reproducibility without reintroducing
unreviewed content into the release control plane.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable


STEP16 = {
    "00-snapshot-inventory": ("processing/migration/",),
    "01-physical-csv": ("standardized/csv-data/",),
    "02-source-evidence": (
        "processing/derived/csv/manifests/source_evidence.csv",
        "processing/derived/csv/manifests/export_partitions.csv",
    ),
    "03-logical-assembly": ("processing/derived/csv/manifests/",),
    "04-field-profiling": ("standardized/derived/csv/schema/",),
}

STEP17 = {
    "05-model-projection": ("processing/derived/yonod/datasets/",),
    "06-target-adaptation": ("processing/derived/yonod/datasets/",),
    "07-validation-configs": (
        "processing/derived/yonod/formal_configs/",
        "processing/derived/yonod/extended_formal_configs/",
        "processing/derived/yonod/review_configs/",
        "processing/derived/yonod/tasks/",
        "processing/derived/yonod/testsets/",
    ),
    "08-runs-and-reports": (
        "processing/derived/yonod/reports/",
        "processing/derived/yonod/markdown_reports/",
        "processing/derived/yonod/native_results/",
        "processing/derived/yonod/logs/",
        "processing/derived/yonod/batch16_runs/",
        "processing/derived/yonod/sequential_two_runs/",
    ),
}

HEADER = [
    "archive_stage", "artifact_id", "old_path", "archive_path", "object_type",
    "size_bytes", "sha256", "disposition", "license_id", "redistribution_status",
    "canonical_artifact_id", "payload_retention", "replacement_relation", "reason",
]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read_inventory(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def matches(path: str, rules: Iterable[str]) -> bool:
    return any(path.startswith(rule) for rule in rules)


def selected(stage: str, rules: tuple[str, ...], inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [row for row in inventory if row["object_type"] != "dir" and matches(row["old_path"], rules)]
    if stage == "05-model-projection":
        rows = [row for row in rows if row["old_path"].endswith("/reactions_model.csv")]
    elif stage == "06-target-adaptation":
        rows = [row for row in rows if not row["old_path"].endswith("/reactions_model.csv")]
    elif stage == "03-logical-assembly":
        rows = [row for row in rows if Path(row["old_path"]).name in {
            "logical_datasets.csv", "logical_dataset_members.csv", "merge_decisions.csv",
            "validation_report.csv",
        }]
    return sorted(rows, key=lambda row: row["old_path"])


def build(stage_set: str, inventory_path: Path, intermediate_root: Path, report_path: Path) -> dict[str, object]:
    definitions = STEP16 if stage_set == "16" else STEP17
    inventory = read_inventory(inventory_path)
    if len(inventory) < 4000:
        raise ValueError("artifact inventory is unexpectedly incomplete")
    physical = 0
    if stage_set == "16":
        physical = sum(
            1 for row in selected("01-physical-csv", STEP16["01-physical-csv"], inventory)
            if Path(row["old_path"]).name.startswith("ord_dataset-") and row["old_path"].endswith(".csv")
        )
        if physical != 53:
            raise ValueError(f"expected 53 physical CSV records, found {physical}")
    stages: list[dict[str, object]] = []
    for stage, rules in definitions.items():
        rows = selected(stage, rules, inventory)
        if not rows:
            raise ValueError(f"no inventory records selected for {stage}")
        destination = intermediate_root / stage / "archive-index.csv"
        if destination.exists():
            raise FileExistsError(f"refusing to overwrite {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=HEADER, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                suffix = row["old_path"].split("/", 1)[1]
                writer.writerow({
                    "archive_stage": stage,
                    "artifact_id": row["artifact_id"],
                    "old_path": row["old_path"],
                    "archive_path": f"intermediate/{stage}/payload/{suffix}",
                    "object_type": row["object_type"],
                    "size_bytes": row["size_bytes"],
                    "sha256": row["sha256"],
                    "disposition": row["disposition"],
                    "license_id": row["license_candidate_id"],
                    "redistribution_status": row["redistribution_status"],
                    "canonical_artifact_id": row["canonical_artifact_id"],
                    "payload_retention": "external-read-only-reference",
                    "replacement_relation": "indexed_without_copy_pending_release_backend_and_content_gate",
                    "reason": "Payload is retained only by content hash and source-relative location; this avoids duplicate bytes and prevents unreviewed legacy content entering regular Git.",
                })
        stages.append({
            "stage": stage,
            "index": str(destination),
            "record_count": len(rows),
            "bytes": sum(int(row["size_bytes"]) for row in rows),
            "sha256": digest(destination),
            "dispositions": dict(sorted(Counter(row["disposition"] for row in rows).items())),
        })
    if stage_set == "16":
        next(item for item in stages if item["stage"] == "01-physical-csv")
    report = {
        "schema_version": "1.0.0", "step_id": f"step-{stage_set}", "status": "complete",
        "payload_policy": "external_read_only_content_addressed_references",
        "input_inventory_sha256": digest(inventory_path), "physical_csv_count": physical,
        "stages": stages,
    }
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite {report_path}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", choices=("16", "17"), required=True)
    parser.add_argument("--artifact-inventory", type=Path, required=True)
    parser.add_argument("--intermediate-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.step, args.artifact_inventory, args.intermediate_root, args.report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
