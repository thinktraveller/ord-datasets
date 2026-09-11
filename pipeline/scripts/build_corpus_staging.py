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
"""Build validated, redacted corpus packages in an explicitly supplied staging root.

Inputs are never modified.  The caller supplies every input and output root so
the script cannot implicitly target a workstation-specific source directory.
Each logical corpus is written to a temporary sibling and atomically promoted
only after its CSV, metadata, links, checksums, membership counts, and
literal-email rescan pass.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sanitize_reaction_json_csv import EMAIL, sanitize

CONTRACT_VERSION = "1.0.0"
CORPUS_HEADER = ["physical_dataset_id", "source_file", "reaction_id", "row_index", "reaction_json"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def write_checksums(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["role", "path", "sha256", "size_bytes"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_json_array(row: dict[str, str], field: str) -> list[str]:
    value = json.loads(row[field])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a JSON string array")
    return value


def count_literal_emails(node: Any) -> int:
    if isinstance(node, dict):
        return sum(count_literal_emails(value) for value in node.values())
    if isinstance(node, list):
        return sum(count_literal_emails(value) for value in node)
    return int(isinstance(node, str) and EMAIL.fullmatch(node) is not None)


def validate_reactions(path: Path, expected_members: dict[tuple[str, str], int], expected_rows: int) -> dict[str, int]:
    observed_members: Counter[tuple[str, str]] = Counter()
    rows = 0
    remaining_emails = 0
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != CORPUS_HEADER:
            raise ValueError(f"unexpected corpus CSV header in {path.name}: {reader.fieldnames!r}")
        for row in reader:
            member = (row["physical_dataset_id"], row["source_file"])
            if member not in expected_members:
                raise ValueError("corpus row references a physical source outside logical membership")
            if not row["reaction_id"]:
                raise ValueError("corpus row has an empty reaction_id")
            try:
                row_index = int(row["row_index"])
            except ValueError as error:
                raise ValueError("corpus row_index is not an integer") from error
            if row_index < 0:
                raise ValueError("corpus row_index must be non-negative")
            try:
                reaction = json.loads(row["reaction_json"])
            except json.JSONDecodeError as error:
                raise ValueError("corpus reaction_json is invalid JSON") from error
            remaining_emails += count_literal_emails(reaction)
            observed_members[member] += 1
            rows += 1
    if rows != expected_rows:
        raise ValueError(f"corpus row count mismatch: {rows} != {expected_rows}")
    if dict(observed_members) != expected_members:
        raise ValueError("corpus source-member row counts do not match logical membership")
    if remaining_emails:
        raise ValueError("redacted corpus still contains literal email values")
    return {"row_count": rows, "remaining_literal_email_values": remaining_emails}


def corpus_schema() -> dict[str, Any]:
    return {
        "schema_version": CONTRACT_VERSION,
        "contract": "pipeline/schemas/csv-contracts.json#corpus_reactions",
        "encoding": "UTF-8",
        "line_ending": "LF",
        "header": CORPUS_HEADER,
        "unique_key": ["physical_dataset_id", "source_file", "reaction_id", "row_index"],
        "sensitive_data_rule": "sanitized_derivative_only",
    }


def build(
    source_root: Path,
    semantic_map_path: Path,
    members_path: Path,
    source_files_path: Path,
    output_root: Path,
    audit_root: Path,
    run_manifest_path: Path,
    schema_dir: Path,
    expected_corpus_count: int = 41,
    expected_reaction_count: int = 2428291,
    expected_physical_count: int = 53,
    resume: bool = False,
) -> dict[str, Any]:
    """Create all corpus directories or fail without promoting a partial directory."""
    if output_root.exists() and any(output_root.iterdir()) and not resume:
        raise ValueError(f"staging output root is not empty: {output_root}")
    if audit_root.exists() and any(audit_root.iterdir()) and not resume:
        raise ValueError(f"staging audit root is not empty: {audit_root}")
    if run_manifest_path.exists():
        raise ValueError(f"run manifest already exists: {run_manifest_path}")
    output_root.mkdir(parents=True, exist_ok=True)
    audit_root.mkdir(parents=True, exist_ok=True)

    semantic_rows = read_csv(semantic_map_path)
    member_rows = read_csv(members_path)
    source_rows = read_csv(source_files_path)
    source_by_physical = {row["physical_dataset_id"]: row for row in source_rows}
    if len(source_by_physical) != len(source_rows):
        raise ValueError("frozen source manifest has duplicate physical_dataset_id")
    members_by_logical: dict[str, list[dict[str, str]]] = {}
    for row in member_rows:
        members_by_logical.setdefault(row["logical_dataset_id"], []).append(row)
    member_physical_ids = [row["physical_dataset_id"] for row in member_rows]
    if len(member_rows) != expected_physical_count or len(set(member_physical_ids)) != expected_physical_count:
        raise ValueError("logical membership must contain each expected physical dataset exactly once")
    if len(source_by_physical) != expected_physical_count or set(member_physical_ids) != set(source_by_physical):
        raise ValueError("logical membership and frozen source manifest do not cover the same physical datasets")
    if len(semantic_rows) != expected_corpus_count:
        raise ValueError(f"semantic map must contain {expected_corpus_count} corpus rows, found {len(semantic_rows)}")
    if {row["logical_dataset_id"] for row in semantic_rows} != set(members_by_logical):
        raise ValueError("semantic corpus rows and logical membership IDs disagree")

    metadata_validator = Draft202012Validator(json.loads((schema_dir / "dataset-metadata.schema.json").read_text(encoding="utf-8")))
    links_validator = Draft202012Validator(json.loads((schema_dir / "source-links.schema.json").read_text(encoding="utf-8")))
    source_manifest_sha256 = sha256(source_files_path)
    package_records: list[dict[str, Any]] = []
    total_rows = 0
    total_removed = 0

    for semantic in sorted(semantic_rows, key=lambda row: row["directory_slug"]):
        logical_id = semantic["logical_dataset_id"]
        slug = semantic["directory_slug"]
        expected_physical_ids = parse_json_array(semantic, "physical_dataset_ids_json")
        expected_source_files = parse_json_array(semantic, "physical_source_files_json")
        members = sorted(members_by_logical[logical_id], key=lambda row: (row["source_file"], row["physical_dataset_id"]))
        expected_members = {(row["physical_dataset_id"], row["source_file"]): int(row["reaction_count"]) for row in members}
        if set(expected_physical_ids) != {physical for physical, _ in expected_members}:
            raise ValueError(f"semantic map physical IDs disagree with membership for {logical_id}")
        if set(expected_source_files) != {source_file for _, source_file in expected_members}:
            raise ValueError(f"semantic map source files disagree with membership for {logical_id}")
        expected_rows = int(semantic["reaction_count"])
        if expected_rows != sum(expected_members.values()):
            raise ValueError(f"semantic map reaction count disagrees with membership for {logical_id}")
        source_csv = source_root / f"logical_dataset_id={logical_id}" / "reactions.csv"
        if not source_csv.is_file():
            raise FileNotFoundError(f"missing logical CSV: {source_csv}")

        partial_dir = output_root / f".{slug}.partial"
        final_dir = output_root / slug
        redaction_audit_path = audit_root / f"{slug}.json"
        if partial_dir.exists():
            raise ValueError(f"refusing to overwrite staged corpus directory: {slug}")
        if final_dir.exists():
            if not resume:
                raise ValueError(f"refusing to overwrite staged corpus directory: {slug}")
            if not redaction_audit_path.is_file():
                raise ValueError(f"existing staged corpus lacks its redaction audit: {slug}")
            if json.loads((final_dir / "schema.json").read_text(encoding="utf-8")) != corpus_schema():
                raise ValueError(f"existing staged corpus has an unexpected local schema: {slug}")
            existing_links = json.loads((final_dir / "source-links.json").read_text(encoding="utf-8"))
            links_validator.validate(existing_links)
            if existing_links["logical_dataset_id"] != logical_id or {link["physical_dataset_id"] for link in existing_links["links"]} != set(expected_physical_ids):
                raise ValueError(f"existing staged corpus source links disagree with semantic membership: {slug}")
            for link in existing_links["links"]:
                frozen = source_by_physical[link["physical_dataset_id"]]
                if any(link[field] != frozen[source_field] for field, source_field in (("source_file", "upstream_path"), ("upstream_revision", "upstream_revision"), ("source_file_url", "source_file_url"), ("source_sha256", "source_sha256"), ("git_lfs_oid", "git_lfs_oid"), ("data_license_id", "data_license_id"))):
                    raise ValueError(f"existing staged source link disagrees with frozen manifest: {slug}")
            existing_metadata = json.loads((final_dir / "metadata.json").read_text(encoding="utf-8"))
            metadata_validator.validate(existing_metadata)
            if existing_metadata["logical_dataset_id"] != logical_id or existing_metadata["dataset_slug"] != slug or existing_metadata["corpus_row_count"] != expected_rows:
                raise ValueError(f"existing staged metadata disagrees with semantic map: {slug}")
            checksum_files = {"reactions": "reactions.csv", "schema": "schema.json", "source-links": "source-links.json"}
            with (final_dir / "checksums.csv").open(encoding="utf-8", newline="") as handle:
                checksum_rows = list(csv.DictReader(handle))
            if {row["role"] for row in checksum_rows} != set(checksum_files):
                raise ValueError(f"existing staged checksums have an unexpected role set: {slug}")
            for checksum in checksum_rows:
                filename = checksum_files[checksum["role"]]
                if checksum["path"] != filename or checksum["sha256"] != sha256(final_dir / filename) or int(checksum["size_bytes"]) != (final_dir / filename).stat().st_size:
                    raise ValueError(f"existing staged checksum mismatch: {slug}/{filename}")
            audit = json.loads(redaction_audit_path.read_text(encoding="utf-8"))
            reaction_validation = validate_reactions(final_dir / "reactions.csv", expected_members, expected_rows)
            if audit.get("output_sha256") != sha256(final_dir / "reactions.csv") or audit.get("row_count") != expected_rows:
                raise ValueError(f"existing staged redaction audit disagrees with output: {slug}")
            audit_summary = {key: audit[key] for key in ("input_sha256", "output_sha256", "row_count", "email_values_removed", "redacted_json_paths")}
            package_records.append({"logical_dataset_id": logical_id, "dataset_slug": slug, "row_count": reaction_validation["row_count"], "remaining_literal_email_values": reaction_validation["remaining_literal_email_values"], "redaction_audit": f"sensitive-redaction-audits/{slug}.json", "redaction": audit_summary, "artifacts": {filename: {"sha256": sha256(final_dir / filename), "size_bytes": (final_dir / filename).stat().st_size} for filename in ("reactions.csv", "schema.json", "source-links.json", "checksums.csv", "metadata.json")}})
            total_rows += expected_rows
            total_removed += int(audit["email_values_removed"])
            continue
        partial_dir.mkdir()
        try:
            write_json(partial_dir / "schema.json", corpus_schema())
            link_rows = []
            for member in members:
                frozen = source_by_physical.get(member["physical_dataset_id"])
                if frozen is None or frozen["upstream_path"] != member["source_file"]:
                    raise ValueError(f"membership source has no matching frozen source record for {logical_id}")
                link_rows.append(
                    {
                        "physical_dataset_id": frozen["physical_dataset_id"],
                        "source_file": frozen["upstream_path"],
                        "upstream_revision": frozen["upstream_revision"],
                        "source_file_url": frozen["source_file_url"],
                        "source_sha256": frozen["source_sha256"],
                        "git_lfs_oid": frozen["git_lfs_oid"],
                        "size_bytes": int(frozen["size_bytes"]),
                        "reaction_count": int(frozen["reaction_count"]),
                        "data_license_id": frozen["data_license_id"],
                        "verification_status": frozen["verification_status"],
                    }
                )
            source_links = {"schema_version": CONTRACT_VERSION, "logical_dataset_id": logical_id, "source_manifest_path": "provenance/source-files.initial.csv", "links": link_rows}
            links_validator.validate(source_links)
            write_json(partial_dir / "source-links.json", source_links)

            audit = sanitize(source_csv, partial_dir / "reactions.csv", redaction_audit_path)
            reaction_validation = validate_reactions(partial_dir / "reactions.csv", expected_members, expected_rows)
            if audit["row_count"] != expected_rows:
                raise ValueError("sanitizer row count disagrees with logical mapping")
            checksum_inputs = []
            for role, filename in (("reactions", "reactions.csv"), ("schema", "schema.json"), ("source-links", "source-links.json")):
                artifact = partial_dir / filename
                checksum_inputs.append({"role": role, "path": filename, "sha256": sha256(artifact), "size_bytes": artifact.stat().st_size})
            write_checksums(partial_dir / "checksums.csv", checksum_inputs)
            metadata_artifacts = [dict(item) for item in checksum_inputs if item["role"] != "source-links"]
            for artifact in metadata_artifacts:
                artifact["path"] = f"datasets/corpus/{slug}/{artifact['path']}"
            metadata_artifacts.append({"role": "checksums", "path": f"datasets/corpus/{slug}/checksums.csv", "sha256": sha256(partial_dir / "checksums.csv"), "size_bytes": (partial_dir / "checksums.csv").stat().st_size})
            upstream_revisions = {link["upstream_revision"] for link in link_rows}
            if len(upstream_revisions) != 1:
                raise ValueError("logical corpus source links must use one frozen upstream revision")
            metadata = {
                "schema_version": CONTRACT_VERSION,
                "dataset_kind": "corpus",
                "dataset_slug": slug,
                "display_name_en": semantic["display_name_en"],
                "display_name_zh": semantic["display_name_zh"],
                "logical_dataset_id": logical_id,
                "physical_dataset_ids": expected_physical_ids,
                "source_links_path": f"datasets/corpus/{slug}/source-links.json",
                "license_id": "CC-BY-SA-4.0",
                "artifact_status": "staged",
                "readiness_status": "complete_corpus_pending_release_validation",
                "corpus_row_count": expected_rows,
                "target_id": None,
                "label": None,
                "included_count": None,
                "excluded_count": None,
                "content_artifacts": metadata_artifacts,
                "input_provenance": {"ord_upstream_revision": upstream_revisions.pop(), "source_manifest_sha256": source_manifest_sha256, "semantic_name_policy_version": semantic["naming_policy_version"], "provenance_schema_version": CONTRACT_VERSION, "pipeline_commit": None},
            }
            metadata_validator.validate(metadata)
            write_json(partial_dir / "metadata.json", metadata)
            audit_summary = {key: audit[key] for key in ("input_sha256", "output_sha256", "row_count", "email_values_removed", "redacted_json_paths")}
            package_records.append(
                {
                    "logical_dataset_id": logical_id,
                    "dataset_slug": slug,
                    "row_count": reaction_validation["row_count"],
                    "remaining_literal_email_values": reaction_validation["remaining_literal_email_values"],
                    "redaction_audit": f"sensitive-redaction-audits/{slug}.json",
                    "redaction": audit_summary,
                    "artifacts": {filename: {"sha256": sha256(partial_dir / filename), "size_bytes": (partial_dir / filename).stat().st_size} for filename in ("reactions.csv", "schema.json", "source-links.json", "checksums.csv", "metadata.json")},
                }
            )
            total_rows += expected_rows
            total_removed += int(audit["email_values_removed"])
            os.replace(partial_dir, final_dir)
        except Exception:
            if partial_dir.exists():
                shutil.rmtree(partial_dir)
            raise

    if len(package_records) != expected_corpus_count or total_rows != expected_reaction_count:
        raise AssertionError("staged corpus aggregate does not match its frozen count baseline")
    run_manifest = {
        "schema_version": CONTRACT_VERSION,
        "step_id": "step-11",
        "status": "complete",
        "input_hashes": {"semantic_name_map": sha256(semantic_map_path), "logical_dataset_members": sha256(members_path), "source_files_manifest": source_manifest_sha256},
        "corpus_count": len(package_records),
        "reaction_count": total_rows,
        "email_values_removed": total_removed,
        "packages": package_records,
    }
    write_json(run_manifest_path, run_manifest)
    return {"corpus_count": len(package_records), "reaction_count": total_rows, "email_values_removed": total_removed}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--semantic-map", required=True, type=Path)
    parser.add_argument("--members", required=True, type=Path)
    parser.add_argument("--source-files", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--audit-root", required=True, type=Path)
    parser.add_argument("--run-manifest", required=True, type=Path)
    parser.add_argument("--schema-dir", required=True, type=Path)
    parser.add_argument("--resume", action="store_true", help="verify completed corpus directories and continue without rewriting them")
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                source_root=args.source_root,
                semantic_map_path=args.semantic_map,
                members_path=args.members,
                source_files_path=args.source_files,
                output_root=args.output_root,
                audit_root=args.audit_root,
                run_manifest_path=args.run_manifest,
                schema_dir=args.schema_dir,
                resume=args.resume,
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
