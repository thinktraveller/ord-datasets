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
"""Stage 19 semantic model-ready packages from immutable processing outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

VERSION = "1.0.0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def copy(source: Path, destination: Path) -> None:
    shutil.copyfile(source, destination)
    if sha256(source) != sha256(destination):
        raise ValueError(f"copied file hash mismatch: {source.name}")


def parse_array(row: dict[str, str], field: str) -> list[str]:
    value = json.loads(row[field])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"target map {field} must be a JSON string array")
    return value


def enrich_exclusions(source: Path, audit: Path, output: Path) -> tuple[int, str]:
    decision_by_reaction: dict[str, str] = {}
    with audit.open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            key = item["reaction_key"]
            decision = item["label_decision_id"]
            if key in decision_by_reaction:
                raise ValueError("duplicate reaction_key in target audit")
            decision_by_reaction[key] = decision
    count = 0
    with source.open(encoding="utf-8", newline="") as input_handle, output.open("w", encoding="utf-8", newline="") as output_handle:
        reader = csv.DictReader(input_handle)
        required = ["reaction_key", "physical_dataset_id", "source_row_index", "reason"]
        if reader.fieldnames is None or any(field not in reader.fieldnames for field in required):
            raise ValueError("source exclusions lacks required lineage columns")
        fieldnames = ["reaction_key", "physical_dataset_id", "source_row_index", "label_decision_id", "exclusion_reason"]
        writer = csv.DictWriter(output_handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in reader:
            decision = decision_by_reaction.get(row["reaction_key"])
            if decision is None:
                raise ValueError("excluded reaction has no target-audit label decision")
            writer.writerow({"reaction_key": row["reaction_key"], "physical_dataset_id": row["physical_dataset_id"], "source_row_index": row["source_row_index"], "label_decision_id": decision, "exclusion_reason": row["reason"]})
            count += 1
    return count, sha256(source)


def write_checksums(directory: Path, names: dict[str, str]) -> None:
    with (directory / "checksums.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["role", "path", "sha256", "size_bytes"], lineterminator="\n")
        writer.writeheader()
        for role, name in names.items():
            path = directory / name
            writer.writerow({"role": role, "path": name, "sha256": sha256(path), "size_bytes": path.stat().st_size})


def build(
    processing_root: Path,
    standardized_root: Path,
    target_map_path: Path,
    corpus_map_path: Path,
    source_files_path: Path,
    schema_dir: Path,
    output_root: Path,
    run_manifest_path: Path,
) -> dict[str, Any]:
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError("model-ready staging output root is not empty")
    if run_manifest_path.exists():
        raise FileExistsError("model-ready staging run manifest already exists")
    output_root.mkdir(parents=True, exist_ok=True)
    targets = csv_rows(target_map_path)
    corpus_by_logical = {row["logical_dataset_id"]: row for row in csv_rows(corpus_map_path)}
    source_by_id = {row["physical_dataset_id"]: row for row in csv_rows(source_files_path)}
    if len(targets) != 19 or len({row["target_id"] for row in targets}) != 19 or len({row["target_slug"] for row in targets}) != 19:
        raise ValueError("semantic target map must contain 19 unique target IDs and slugs")
    metadata_validator = Draft202012Validator(json.loads((schema_dir / "dataset-metadata.schema.json").read_text(encoding="utf-8")))
    links_validator = Draft202012Validator(json.loads((schema_dir / "source-links.schema.json").read_text(encoding="utf-8")))
    source_manifest_hash = sha256(source_files_path)
    records = []

    for row in sorted(targets, key=lambda item: item["target_slug"]):
        target_id, slug, logical_id = row["target_id"], row["target_slug"], row["logical_dataset_id"]
        physical_ids = parse_array(row, "physical_dataset_ids_json")
        source_files = parse_array(row, "physical_source_files_json")
        if logical_id not in corpus_by_logical or len(set(physical_ids)) != len(physical_ids):
            raise ValueError(f"invalid source set for target {target_id}")
        processing_dir = processing_root / logical_id / "targets" / target_id
        standardized_dir = standardized_root / logical_id / "targets" / target_id
        manifest_source = processing_dir / "target_manifest.json"
        audit_source = processing_dir / "target_audit.jsonl"
        exclusions_source = processing_dir / "exclusions.csv"
        row_map_source = processing_dir / "row_map.csv"
        dataset_sources = list(standardized_dir.glob("*_normalized_dataset.csv"))
        config_sources = list(standardized_dir.glob("*_yonod_config.json"))
        schema_source = standardized_dir / "schema.json"
        if not all(path.is_file() for path in (manifest_source, audit_source, exclusions_source, row_map_source, schema_source)) or len(dataset_sources) != 1 or len(config_sources) != 1:
            raise FileNotFoundError(f"target input set is incomplete for {target_id}")
        manifest = json.loads(manifest_source.read_text(encoding="utf-8"))
        if manifest["target_id"] != target_id or manifest["logical_dataset_id"] != logical_id or manifest["physical_dataset_ids"] != physical_ids:
            raise ValueError(f"target manifest identity mismatch for {target_id}")
        if sha256(manifest_source) != row["target_manifest_sha256"] or sha256(schema_source) != row["standardized_schema_sha256"]:
            raise ValueError(f"frozen target-manifest/schema hash mismatch for {target_id}")
        source_outputs = {"dataset": dataset_sources[0], "yonod-config": config_sources[0], "schema": schema_source, "row-map": row_map_source, "audit": audit_source}
        for source in source_outputs.values():
            if manifest["outputs"].get(source.name) != sha256(source):
                raise ValueError(f"target manifest does not verify {source.name} for {target_id}")
        if manifest["outputs"].get("exclusions.csv") != sha256(exclusions_source):
            raise ValueError(f"target manifest does not verify exclusions.csv for {target_id}")

        final_dir, partial_dir = output_root / slug, output_root / f".{slug}.partial"
        if final_dir.exists() or partial_dir.exists():
            raise FileExistsError(f"refusing to overwrite target staging directory: {slug}")
        partial_dir.mkdir()
        try:
            names = {"dataset": "dataset.csv", "schema": "schema.json", "yonod-config": "yonod-config.json", "row-map": "row-map.csv", "audit": "audit.jsonl"}
            for role, source in source_outputs.items():
                copy(source, partial_dir / names[role])
            excluded_count, raw_exclusions_hash = enrich_exclusions(exclusions_source, audit_source, partial_dir / "exclusions.csv")
            if excluded_count != int(row["excluded_count"]):
                raise ValueError(f"enriched exclusions count mismatch for {target_id}")
            links = []
            for physical_id, source_file in zip(physical_ids, source_files, strict=True):
                frozen = source_by_id.get(physical_id)
                if frozen is None or frozen["upstream_path"] != source_file:
                    raise ValueError(f"frozen source mismatch for target {target_id}")
                links.append({"physical_dataset_id": physical_id, "source_file": source_file, "upstream_revision": frozen["upstream_revision"], "source_file_url": frozen["source_file_url"], "source_sha256": frozen["source_sha256"], "git_lfs_oid": frozen["git_lfs_oid"], "size_bytes": int(frozen["size_bytes"]), "reaction_count": int(frozen["reaction_count"]), "data_license_id": frozen["data_license_id"], "verification_status": frozen["verification_status"]})
            source_links = {"schema_version": VERSION, "logical_dataset_id": logical_id, "source_manifest_path": "provenance/source-files.initial.csv", "links": links}
            links_validator.validate(source_links)
            write_json(partial_dir / "source-links.json", source_links)
            provenance = {"schema_version": VERSION, "target_id": target_id, "logical_dataset_id": logical_id, "target_manifest_sha256": sha256(manifest_source), "input_artifacts": {"normalized_dataset": sha256(dataset_sources[0]), "standardized_schema": sha256(schema_source), "yonod_config": sha256(config_sources[0]), "row_map": sha256(row_map_source), "target_audit": sha256(audit_source), "raw_exclusions": raw_exclusions_hash}, "transformation": {"name": "enrich-exclusions-with-label-decision-id", "output_sha256": sha256(partial_dir / "exclusions.csv")}}
            write_json(partial_dir / "target-build-provenance.json", provenance)
            checksum_names = {**names, "exclusions": "exclusions.csv", "source-links": "source-links.json", "target-build-provenance": "target-build-provenance.json"}
            write_checksums(partial_dir, checksum_names)
            corpus_row_count = int(corpus_by_logical[logical_id]["reaction_count"])
            metadata_artifacts = []
            for role in ("dataset", "schema", "yonod-config", "exclusions", "row-map", "audit"):
                name = checksum_names[role]
                path = partial_dir / name
                metadata_artifacts.append({"role": role, "path": f"datasets/model-ready/{slug}/{name}", "sha256": sha256(path), "size_bytes": path.stat().st_size})
            checksums_path = partial_dir / "checksums.csv"
            metadata_artifacts.append({"role": "checksums", "path": f"datasets/model-ready/{slug}/checksums.csv", "sha256": sha256(checksums_path), "size_bytes": checksums_path.stat().st_size})
            metadata = {"schema_version": VERSION, "dataset_kind": "model-ready", "dataset_slug": slug, "display_name_en": row["display_name_en"], "display_name_zh": row["display_name_zh"], "logical_dataset_id": logical_id, "physical_dataset_ids": physical_ids, "source_links_path": f"datasets/model-ready/{slug}/source-links.json", "license_id": "CC-BY-SA-4.0", "artifact_status": "staged", "readiness_status": row["readiness_status"], "corpus_row_count": corpus_row_count, "target_id": target_id, "label": {"column": row["label_column"], "type": row["label_type"], "unit": row["label_unit"], "policy": row["label_policy"]}, "included_count": int(row["included_count"]), "excluded_count": excluded_count, "content_artifacts": metadata_artifacts, "input_provenance": {"ord_upstream_revision": links[0]["upstream_revision"], "source_manifest_sha256": source_manifest_hash, "semantic_name_policy_version": row["naming_policy_version"], "provenance_schema_version": VERSION, "pipeline_commit": None}}
            metadata_validator.validate(metadata)
            write_json(partial_dir / "metadata.json", metadata)
            records.append({"target_id": target_id, "target_slug": slug, "logical_dataset_id": logical_id, "readiness_status": row["readiness_status"], "included_count": int(row["included_count"]), "excluded_count": excluded_count, "source_count": int(row["source_count"]), "artifacts": {path.name: {"sha256": sha256(path), "size_bytes": path.stat().st_size} for path in sorted(partial_dir.iterdir()) if path.is_file()}})
            os.replace(partial_dir, final_dir)
        except Exception:
            if partial_dir.exists():
                shutil.rmtree(partial_dir)
            raise
    result = {"schema_version": VERSION, "step_id": "step-13", "status": "complete", "input_hashes": {"semantic_target_map": sha256(target_map_path), "semantic_corpus_map": sha256(corpus_map_path), "source_files_manifest": source_manifest_hash}, "target_count": len(records), "included_count": sum(row["included_count"] for row in records), "excluded_count": sum(row["excluded_count"] for row in records), "packages": records}
    write_json(run_manifest_path, result)
    return {key: result[key] for key in ("target_count", "included_count", "excluded_count")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processing-root", required=True, type=Path)
    parser.add_argument("--standardized-root", required=True, type=Path)
    parser.add_argument("--target-map", required=True, type=Path)
    parser.add_argument("--corpus-map", required=True, type=Path)
    parser.add_argument("--source-files", required=True, type=Path)
    parser.add_argument("--schema-dir", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--run-manifest", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                processing_root=args.processing_root,
                standardized_root=args.standardized_root,
                target_map_path=args.target_map,
                corpus_map_path=args.corpus_map,
                source_files_path=args.source_files,
                schema_dir=args.schema_dir,
                output_root=args.output_root,
                run_manifest_path=args.run_manifest,
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
