#!/usr/bin/env python3
"""Index the sanitized model-ready staging evidence into stages 05--08.

This deliberately indexes the authoritative step-13 staging payload rather
than copying older `reactions_model.csv` snapshots from the legacy workspace.
The result is a non-duplicating record of the exact 19 target artifacts that
will be eligible for the configured release data plane.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROUTES = {
    "dataset.csv": "05-model-projection",
    "row-map.csv": "06-target-adaptation",
    "audit.jsonl": "06-target-adaptation",
    "exclusions.csv": "06-target-adaptation",
    "target-build-provenance.json": "06-target-adaptation",
    "metadata.json": "06-target-adaptation",
    "source-links.json": "06-target-adaptation",
    "schema.json": "07-validation-configs",
    "yonod-config.json": "07-validation-configs",
    "checksums.csv": "08-runs-and-reports",
}
HEADER = [
    "archive_stage", "target_slug", "artifact_role", "staging_path", "archive_path",
    "size_bytes", "sha256", "payload_retention", "disposition", "license_id", "reason",
]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def build(staging_root: Path, intermediate_root: Path, report_path: Path) -> dict[str, object]:
    packages = sorted(path for path in staging_root.iterdir() if path.is_dir())
    if len(packages) != 19:
        raise ValueError(f"expected 19 staged target directories, found {len(packages)}")
    records: dict[str, list[dict[str, str]]] = defaultdict(list)
    for package in packages:
        names = {path.name for path in package.iterdir() if path.is_file()}
        if names != set(ROUTES):
            raise ValueError(f"unexpected staged target artifact set for {package.name}: {sorted(names)}")
        for name, stage in ROUTES.items():
            payload = package / name
            records[stage].append({
                "archive_stage": stage, "target_slug": package.name, "artifact_role": name,
                "staging_path": f".staging/ord-datasets-v0/step-13/datasets/model-ready/{package.name}/{name}",
                "archive_path": f"intermediate/{stage}/payload/{package.name}/{name}",
                "size_bytes": str(payload.stat().st_size), "sha256": digest(payload),
                "payload_retention": "staging-content-addressed-reference",
                "disposition": "intermediate",
                "license_id": "CC-BY-SA-4.0",
                "reason": "Exact sanitized step-13 target artifact retained by hash reference; payload is not copied into regular Git.",
            })
    summaries = []
    for stage in sorted(set(ROUTES.values())):
        output = intermediate_root / stage / "archive-index.csv"
        if output.exists():
            raise FileExistsError(f"refusing to overwrite {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=HEADER, lineterminator="\n")
            writer.writeheader()
            writer.writerows(sorted(records[stage], key=lambda row: (row["target_slug"], row["artifact_role"])))
        summaries.append({
            "stage": stage, "record_count": len(records[stage]),
            "bytes": sum(int(row["size_bytes"]) for row in records[stage]), "sha256": digest(output),
        })
    report = {
        "schema_version": "1.0.0", "step_id": "step-17", "status": "complete",
        "target_count": len(packages), "package_count": 15,
        "payload_policy": "sanitized_staging_content_addressed_references", "stages": summaries,
    }
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite {report_path}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-root", required=True, type=Path)
    parser.add_argument("--intermediate-root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.staging_root, args.intermediate_root, args.report), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
