#!/usr/bin/env python3
"""Build fixed-revision source, dataset, membership, package and target maps."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, header: list[str], rows: list[dict[str, Any]]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(source_path: Path, semantic_path: Path, target_path: Path, members_path: Path, output_root: Path) -> dict[str, Any]:
    sources = read_csv(source_path)
    semantic = read_csv(semantic_path)
    targets = read_csv(target_path)
    members = read_csv(members_path)
    if len(sources) != 53 or len(semantic) != 41 or len(targets) != 19 or len(members) != 53:
        raise ValueError("frozen provenance input cardinality is not 53/41/19/53")
    source_by_id = {row["physical_dataset_id"]: row for row in sources}
    if len(source_by_id) != 53 or len({row["physical_dataset_id"] for row in members}) != 53:
        raise ValueError("physical source or membership identity is not unique")
    if any("/blob/main/" in row["source_file_url"] for row in sources):
        raise ValueError("source manifest contains a mutable main URL")
    if any(row["upstream_revision"] not in row["source_file_url"] for row in sources):
        raise ValueError("source manifest contains a non-pinned source URL")

    output_root.mkdir(parents=True, exist_ok=True)
    source_out = output_root / "source-files.csv"
    if source_out.exists():
        raise FileExistsError(f"refusing to overwrite {source_out}")
    source_out.write_bytes(source_path.read_bytes())
    physical_rows = []
    for row in sources:
        physical_rows.append({
            "physical_dataset_id": row["physical_dataset_id"],
            "source_file_id": row["source_file_id"],
            "upstream_path": row["upstream_path"],
            "source_file_url": row["source_file_url"],
            "upstream_revision": row["upstream_revision"],
            "source_sha256": row["source_sha256"],
            "git_lfs_oid": row["git_lfs_oid"], "size_bytes": row["size_bytes"],
            "reaction_count": row["reaction_count"], "license_id": row["data_license_id"],
            "verification_status": row["verification_status"],
        })
    write_csv(output_root / "physical-datasets.csv", list(physical_rows[0]), physical_rows)
    logical_rows = []
    for row in semantic:
        physical_ids = json.loads(row["physical_dataset_ids_json"])
        logical_rows.append({
            "logical_dataset_id": row["logical_dataset_id"], "dataset_slug": row["directory_slug"],
            "display_name_en": row["display_name_en"], "display_name_zh": row["display_name_zh"],
            "relationship": row["relationship"], "physical_dataset_ids_json": row["physical_dataset_ids_json"],
            "member_count": row["member_count"], "reaction_count": row["reaction_count"],
            "license_id": "CC-BY-SA-4.0", "naming_policy_version": row["naming_policy_version"],
            "source_url_count": len(physical_ids),
        })
    write_csv(output_root / "logical-datasets.csv", list(logical_rows[0]), logical_rows)
    member_rows = []
    for member in members:
        source = source_by_id.get(member["physical_dataset_id"])
        if source is None or source["upstream_path"] != member["source_file"]:
            raise ValueError(f"membership source mismatch for {member['physical_dataset_id']}")
        member_rows.append({
            "logical_dataset_id": member["logical_dataset_id"],
            "physical_dataset_id": member["physical_dataset_id"], "source_file": member["source_file"],
            "reaction_count": member["reaction_count"], "relationship": member["relationship"],
            "source_file_url": source["source_file_url"], "source_sha256": source["source_sha256"],
            "upstream_revision": source["upstream_revision"],
        })
    write_csv(output_root / "logical-dataset-members.csv", list(member_rows[0]), member_rows)
    target_rows = []
    for row in targets:
        target_rows.append({
            "target_id": row["target_id"], "target_slug": row["target_slug"],
            "logical_dataset_id": row["logical_dataset_id"],
            "physical_dataset_ids_json": row["physical_dataset_ids_json"],
            "label_column": row["label_column"], "label_type": row["label_type"],
            "label_unit": row["label_unit"], "included_count": row["included_count"],
            "excluded_count": row["excluded_count"], "source_count": row["source_count"],
            "readiness_status": row["readiness_status"], "artifact_status": row["artifact_status"],
            "target_manifest_sha256": row["target_manifest_sha256"],
        })
    write_csv(output_root / "target-datasets.csv", list(target_rows[0]), target_rows)
    package_ids = sorted({row["logical_dataset_id"] for row in targets})
    if len(package_ids) != 15:
        raise ValueError(f"expected 15 model packages, found {len(package_ids)}")
    package_rows = []
    for package_id in package_ids:
        package_targets = [row for row in target_rows if row["logical_dataset_id"] == package_id]
        package_rows.append({
            "package_id": package_id, "target_count": len(package_targets),
            "target_ids_json": json.dumps([row["target_id"] for row in package_targets]),
            "target_statuses_json": json.dumps([row["readiness_status"] for row in package_targets]),
        })
    write_csv(output_root / "package-datasets.csv", list(package_rows[0]), package_rows)
    evidence_rows = [{
        "physical_dataset_id": row["physical_dataset_id"], "source_file": row["upstream_path"],
        "source_file_url": row["source_file_url"], "source_sha256": row["source_sha256"],
        "evidence_location": "intermediate/02-source-evidence/archive-index.csv",
    } for row in sources]
    write_csv(output_root / "source-evidence.csv", list(evidence_rows[0]), evidence_rows)
    outputs = [source_out, output_root / "physical-datasets.csv", output_root / "logical-datasets.csv",
               output_root / "logical-dataset-members.csv", output_root / "target-datasets.csv",
               output_root / "package-datasets.csv", output_root / "source-evidence.csv"]
    return {
        "schema_version": "1.0.0", "step_id": "step-21", "status": "complete",
        "physical_sources": 53, "logical_corpora": 41, "logical_memberships": 53,
        "model_packages": 15, "model_ready_targets": 19, "unpinned_main_urls": 0,
        "outputs": {path.name: digest(path) for path in outputs},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-files", type=Path, required=True)
    parser.add_argument("--semantic-map", type=Path, required=True)
    parser.add_argument("--target-map", type=Path, required=True)
    parser.add_argument("--members", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source_files, args.semantic_map, args.target_map, args.members, args.output_root)
    if args.report.exists():
        raise FileExistsError(f"refusing to overwrite {args.report}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
