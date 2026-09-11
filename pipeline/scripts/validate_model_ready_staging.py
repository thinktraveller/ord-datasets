#!/usr/bin/env python3
# Copyright 2026 ord-datasets contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Validate all staged model-ready packages without rewriting data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

FILES = {"dataset.csv", "schema.json", "yonod-config.json", "row-map.csv", "audit.jsonl", "exclusions.csv", "source-links.json", "target-build-provenance.json", "checksums.csv", "metadata.json"}
CHECKSUM_NAMES = {"dataset": "dataset.csv", "schema": "schema.json", "yonod-config": "yonod-config.json", "row-map": "row-map.csv", "audit": "audit.jsonl", "exclusions": "exclusions.csv", "source-links": "source-links.json", "target-build-provenance": "target-build-provenance.json"}
ROW_MAP_HEADER = ["csv_row_number", "reaction_key", "physical_dataset_id", "source_row_index", "label_decision_id"]
EXCLUSIONS_HEADER = ["reaction_key", "physical_dataset_id", "source_row_index", "label_decision_id", "exclusion_reason"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(staging_root: Path, target_map_path: Path, source_files_path: Path, schema_dir: Path, control_manifest_path: Path) -> dict[str, Any]:
    target_map = rows(target_map_path)
    source_by_id = {row["physical_dataset_id"]: row for row in rows(source_files_path)}
    if len(target_map) != 19 or len({row["target_slug"] for row in target_map}) != 19:
        raise ValueError("semantic target map must have 19 unique rows")
    expected_slugs = {row["target_slug"] for row in target_map}
    actual_slugs = {path.name for path in staging_root.iterdir() if path.is_dir() and not path.name.startswith(".")}
    if actual_slugs != expected_slugs or list(staging_root.glob(".*.partial")):
        raise ValueError("staging target directories do not match semantic map")
    metadata_validator = Draft202012Validator(load(schema_dir / "dataset-metadata.schema.json"))
    links_validator = Draft202012Validator(load(schema_dir / "source-links.schema.json"))
    control = load(control_manifest_path)
    control_by_slug = {row["target_slug"]: row for row in control["packages"]}
    if control.get("status") != "staging_complete_not_released" or set(control_by_slug) != expected_slugs:
        raise ValueError("target control manifest does not match staging")
    result_rows = []
    total_included = total_excluded = 0
    for target in sorted(target_map, key=lambda row: row["target_slug"]):
        slug, target_id, logical_id = target["target_slug"], target["target_id"], target["logical_dataset_id"]
        directory = staging_root / slug
        if {path.name for path in directory.iterdir() if path.is_file()} != FILES:
            raise ValueError(f"unexpected file set in {slug}")
        checksums = {row["role"]: row for row in rows(directory / "checksums.csv")}
        if set(checksums) != set(CHECKSUM_NAMES):
            raise ValueError(f"unexpected checksum roles in {slug}")
        for role, name in CHECKSUM_NAMES.items():
            current = directory / name
            item = checksums[role]
            if item["path"] != name or item["sha256"] != sha256(current) or int(item["size_bytes"]) != current.stat().st_size:
                raise ValueError(f"checksum mismatch in {slug}/{name}")
        metadata = load(directory / "metadata.json")
        metadata_validator.validate(metadata)
        if metadata["target_id"] != target_id or metadata["logical_dataset_id"] != logical_id or metadata["readiness_status"] != target["readiness_status"] or metadata["label"]["column"] != target["label_column"] or metadata["label"]["type"] != target["label_type"]:
            raise ValueError(f"metadata semantic/status mismatch in {slug}")
        artifacts = {item["role"]: item for item in metadata["content_artifacts"]}
        for role in ("dataset", "schema", "yonod-config", "row-map", "audit", "exclusions", "checksums"):
            name = "checksums.csv" if role == "checksums" else CHECKSUM_NAMES[role]
            if role not in artifacts or artifacts[role]["sha256"] != sha256(directory / name) or artifacts[role]["size_bytes"] != (directory / name).stat().st_size:
                raise ValueError(f"metadata artifact mismatch in {slug}/{name}")
        links = load(directory / "source-links.json")
        links_validator.validate(links)
        expected_ids = json.loads(target["physical_dataset_ids_json"])
        if links["logical_dataset_id"] != logical_id or {link["physical_dataset_id"] for link in links["links"]} != set(expected_ids):
            raise ValueError(f"source-link target membership mismatch in {slug}")
        for link in links["links"]:
            frozen = source_by_id[link["physical_dataset_id"]]
            if link["source_file"] != frozen["upstream_path"] or link["source_file_url"] != frozen["source_file_url"] or link["source_sha256"] != frozen["source_sha256"] or "/blob/main/" in link["source_file_url"]:
                raise ValueError(f"unpinned or drifting source link in {slug}")
        schema = load(directory / "schema.json")
        if schema.get("column_roles", {}).get("label") != target["label_column"]:
            raise ValueError(f"target label column mismatch in schema: {slug}")
        dataset_rows = rows(directory / "dataset.csv")
        dataset_header = set(dataset_rows[0]) if dataset_rows else set(next(csv.DictReader((directory / "dataset.csv").open(encoding="utf-8", newline=""), []), []))
        if target["label_column"] not in dataset_header:
            raise ValueError(f"dataset label is absent in {slug}")
        feature_columns = set(schema.get("feature_columns", [])) | set(schema.get("column_roles", {}).get("features", []))
        if target["label_column"] in feature_columns:
            raise ValueError(f"label leakage in declared feature columns: {slug}")
        row_map = rows(directory / "row-map.csv")
        exclusions = rows(directory / "exclusions.csv")
        if (row_map and list(row_map[0])[:len(ROW_MAP_HEADER)] != ROW_MAP_HEADER) or (row_map and set(row_map[0]) - set(ROW_MAP_HEADER) - {"campaign_id"}) or (exclusions and list(exclusions[0]) != EXCLUSIONS_HEADER):
            raise ValueError(f"row-map or exclusions header mismatch in {slug}")
        included, excluded, source_count = int(target["included_count"]), int(target["excluded_count"]), int(target["source_count"])
        if len(dataset_rows) != included or len(row_map) != included or len(exclusions) != excluded or included + excluded != source_count:
            raise ValueError(f"included/excluded/source count mismatch in {slug}")
        audit_by_key = {}
        with (directory / "audit.jsonl").open(encoding="utf-8") as handle:
            for line in handle:
                item = json.loads(line)
                if item["reaction_key"] in audit_by_key:
                    raise ValueError(f"duplicate audit reaction key in {slug}")
                audit_by_key[item["reaction_key"]] = item
        if len(audit_by_key) != source_count:
            raise ValueError(f"audit count mismatch in {slug}")
        row_numbers = set()
        row_keys = set()
        for item in row_map:
            number, key = int(item["csv_row_number"]), item["reaction_key"]
            physical, index = item["physical_dataset_id"], int(item["source_row_index"])
            if number < 1 or number in row_numbers or key in row_keys or physical not in expected_ids or index < 0 or index >= int(source_by_id[physical]["reaction_count"]):
                raise ValueError(f"invalid row-map lineage in {slug}")
            audit = audit_by_key.get(key)
            if audit is None or audit["status"] != "included" or audit["label_decision_id"] != item["label_decision_id"]:
                raise ValueError(f"row-map decision mismatch in {slug}")
            row_numbers.add(number); row_keys.add(key)
        for item in exclusions:
            audit = audit_by_key.get(item["reaction_key"])
            if audit is None or audit["status"] != "excluded" or audit["label_decision_id"] != item["label_decision_id"]:
                raise ValueError(f"exclusion decision mismatch in {slug}")
        provenance = load(directory / "target-build-provenance.json")
        if provenance["target_id"] != target_id or provenance["target_manifest_sha256"] != target["target_manifest_sha256"] or provenance["input_artifacts"]["standardized_schema"] != target["standardized_schema_sha256"]:
            raise ValueError(f"target build provenance mismatch in {slug}")
        controlled = control_by_slug[slug]
        if controlled["included_count"] != included or controlled["excluded_count"] != excluded or controlled["artifacts"]["dataset.csv"]["sha256"] != sha256(directory / "dataset.csv"):
            raise ValueError(f"control manifest mismatch in {slug}")
        result_rows.append({"target_id": target_id, "target_slug": slug, "readiness_status": target["readiness_status"], "included_count": included, "excluded_count": excluded, "dataset_sha256": sha256(directory / "dataset.csv"), "remaining_label_leaks": 0})
        total_included += included; total_excluded += excluded
    return {"schema_version": "1.0.0", "step_id": "step-14", "status": "complete", "input_hashes": {"semantic_target_map": sha256(target_map_path), "source_files_manifest": sha256(source_files_path), "control_manifest": sha256(control_manifest_path)}, "target_count": len(result_rows), "included_count": total_included, "excluded_count": total_excluded, "status_mismatches": 0, "row_map_errors": 0, "source_index_errors": 0, "label_leaks": 0, "unpinned_main_urls": 0, "packages": result_rows}


def write_reports(summary: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    if json_path.exists() or markdown_path.exists():
        raise FileExistsError("refusing to overwrite target validation reports")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text("# Model-ready staging validation\n\n" + "\n".join(f"- {key}: `{summary[key]}`" for key in ("status", "target_count", "included_count", "excluded_count", "status_mismatches", "row_map_errors", "source_index_errors", "label_leaks", "unpinned_main_urls")) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-root", required=True, type=Path)
    parser.add_argument("--target-map", required=True, type=Path)
    parser.add_argument("--source-files", required=True, type=Path)
    parser.add_argument("--schema-dir", required=True, type=Path)
    parser.add_argument("--control-manifest", required=True, type=Path)
    parser.add_argument("--json-report", required=True, type=Path)
    parser.add_argument("--markdown-report", required=True, type=Path)
    args = parser.parse_args()
    summary = validate(args.staging_root, args.target_map, args.source_files, args.schema_dir, args.control_manifest)
    write_reports(summary, args.json_report, args.markdown_report)
    print(json.dumps({key: summary[key] for key in ("target_count", "included_count", "excluded_count")}, sort_keys=True))


if __name__ == "__main__":
    main()
