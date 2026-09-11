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
"""Independently validate every staged corpus package without rewriting it."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sanitize_reaction_json_csv import EMAIL

HEADER = ["physical_dataset_id", "source_file", "reaction_id", "row_index", "reaction_json"]
REQUIRED_FILES = {"reactions.csv", "schema.json", "source-links.json", "checksums.csv", "metadata.json"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def literal_email_count(node: Any) -> int:
    if isinstance(node, dict):
        return sum(literal_email_count(value) for value in node.values())
    if isinstance(node, list):
        return sum(literal_email_count(value) for value in node)
    return int(isinstance(node, str) and EMAIL.fullmatch(node) is not None)


def validate_csv(
    path: Path, expected_members: dict[tuple[str, str], int], expected_rows: int
) -> dict[str, int]:
    seen_indices = {member: bytearray(count) for member, count in expected_members.items()}
    member_counts: Counter[tuple[str, str]] = Counter()
    reaction_ids: set[str] = set()
    prior_order: tuple[str, int] | None = None
    row_count = 0
    remaining_emails = 0
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != HEADER:
            raise ValueError(f"unexpected corpus header: {reader.fieldnames!r}")
        for row in reader:
            member = (row["physical_dataset_id"], row["source_file"])
            if member not in expected_members:
                raise ValueError("row references a physical source outside its logical membership")
            try:
                index = int(row["row_index"])
            except ValueError as error:
                raise ValueError("row_index is not an integer") from error
            if index < 0 or index >= expected_members[member]:
                raise ValueError("row_index is outside its physical-source range")
            if seen_indices[member][index]:
                raise ValueError("duplicate physical source row_index")
            seen_indices[member][index] = 1
            if not row["reaction_id"] or row["reaction_id"] in reaction_ids:
                raise ValueError("reaction_id is empty or duplicated within a logical corpus")
            reaction_ids.add(row["reaction_id"])
            order = (row["source_file"], index)
            if prior_order is not None and order < prior_order:
                raise ValueError("rows are not deterministically ordered by source_file and row_index")
            prior_order = order
            try:
                reaction = json.loads(row["reaction_json"])
            except json.JSONDecodeError as error:
                raise ValueError("reaction_json is not valid JSON") from error
            remaining_emails += literal_email_count(reaction)
            member_counts[member] += 1
            row_count += 1
    if row_count != expected_rows or dict(member_counts) != expected_members:
        raise ValueError("corpus row count or physical-member counts mismatch")
    if any(0 in indexes for indexes in seen_indices.values()):
        raise ValueError("a physical source row_index is missing")
    if remaining_emails:
        raise ValueError("literal email value survived corpus redaction")
    return {"row_count": row_count, "remaining_literal_email_values": remaining_emails}


def validate(
    staging_root: Path,
    semantic_map_path: Path,
    members_path: Path,
    source_files_path: Path,
    schema_dir: Path,
    control_manifest_path: Path | None = None,
    expected_corpus_count: int = 41,
    expected_physical_count: int = 53,
    expected_reaction_count: int = 2428291,
) -> dict[str, Any]:
    semantic_rows = csv_rows(semantic_map_path)
    member_rows = csv_rows(members_path)
    source_rows = csv_rows(source_files_path)
    if len(semantic_rows) != expected_corpus_count or len(source_rows) != expected_physical_count:
        raise ValueError("frozen corpus/source counts do not match the expected baseline")
    source_by_id = {row["physical_dataset_id"]: row for row in source_rows}
    physical_ids = [row["physical_dataset_id"] for row in member_rows]
    if len(member_rows) != expected_physical_count or len(set(physical_ids)) != expected_physical_count or set(physical_ids) != set(source_by_id):
        raise ValueError("logical membership does not assign every physical source exactly once")
    members_by_logical: dict[str, list[dict[str, str]]] = {}
    for row in member_rows:
        members_by_logical.setdefault(row["logical_dataset_id"], []).append(row)
    if {row["logical_dataset_id"] for row in semantic_rows} != set(members_by_logical):
        raise ValueError("semantic map and membership logical IDs disagree")
    expected_slugs = {row["directory_slug"] for row in semantic_rows}
    actual_dirs = {path.name for path in staging_root.iterdir() if path.is_dir() and not path.name.startswith(".")}
    if actual_dirs != expected_slugs or list(staging_root.glob(".*.partial")):
        raise ValueError("staging directories do not exactly equal the frozen semantic slug set")

    metadata_validator = Draft202012Validator(load_json(schema_dir / "dataset-metadata.schema.json"))
    links_validator = Draft202012Validator(load_json(schema_dir / "source-links.schema.json"))
    control_by_slug: dict[str, dict[str, Any]] = {}
    control_hash: str | None = None
    if control_manifest_path is not None:
        control = load_json(control_manifest_path)
        if control["status"] != "staging_complete_not_released" or control["corpus_count"] != expected_corpus_count:
            raise ValueError("control manifest does not describe this complete staging run")
        control_by_slug = {row["dataset_slug"]: row for row in control["packages"]}
        if set(control_by_slug) != expected_slugs:
            raise ValueError("control manifest slug set disagrees with staging")
        control_hash = sha256(control_manifest_path)

    results = []
    total_rows = 0
    for semantic in sorted(semantic_rows, key=lambda row: row["directory_slug"]):
        slug = semantic["directory_slug"]
        logical_id = semantic["logical_dataset_id"]
        package_dir = staging_root / slug
        files = {path.name for path in package_dir.iterdir() if path.is_file()}
        if files != REQUIRED_FILES:
            raise ValueError(f"unexpected file set in {slug}")
        local_schema = load_json(package_dir / "schema.json")
        if local_schema.get("header") != HEADER or local_schema.get("contract") != "pipeline/schemas/csv-contracts.json#corpus_reactions":
            raise ValueError(f"local CSV contract mismatch in {slug}")
        links = load_json(package_dir / "source-links.json")
        links_validator.validate(links)
        members = members_by_logical[logical_id]
        expected_members = {(row["physical_dataset_id"], row["source_file"]): int(row["reaction_count"]) for row in members}
        if links["logical_dataset_id"] != logical_id or {link["physical_dataset_id"] for link in links["links"]} != {pair[0] for pair in expected_members}:
            raise ValueError(f"source-link membership mismatch in {slug}")
        for link in links["links"]:
            frozen = source_by_id[link["physical_dataset_id"]]
            for field, frozen_field in (("source_file", "upstream_path"), ("upstream_revision", "upstream_revision"), ("source_file_url", "source_file_url"), ("source_sha256", "source_sha256"), ("git_lfs_oid", "git_lfs_oid"), ("data_license_id", "data_license_id")):
                if link[field] != frozen[frozen_field]:
                    raise ValueError(f"source link disagrees with frozen manifest in {slug}: {field}")
            if "/blob/main/" in link["source_file_url"] or link["upstream_revision"] not in link["source_file_url"]:
                raise ValueError(f"source link is not commit-pinned in {slug}")
        checksums = {row["role"]: row for row in csv_rows(package_dir / "checksums.csv")}
        if set(checksums) != {"reactions", "schema", "source-links"}:
            raise ValueError(f"unexpected checksum roles in {slug}")
        for role, filename in (("reactions", "reactions.csv"), ("schema", "schema.json"), ("source-links", "source-links.json")):
            item = checksums[role]
            if item["path"] != filename or item["sha256"] != sha256(package_dir / filename) or int(item["size_bytes"]) != (package_dir / filename).stat().st_size:
                raise ValueError(f"checksum mismatch in {slug}/{filename}")
        metadata = load_json(package_dir / "metadata.json")
        metadata_validator.validate(metadata)
        expected_rows = int(semantic["reaction_count"])
        if metadata["dataset_slug"] != slug or metadata["logical_dataset_id"] != logical_id or metadata["corpus_row_count"] != expected_rows:
            raise ValueError(f"metadata identity/count mismatch in {slug}")
        metadata_artifacts = {item["role"]: item for item in metadata["content_artifacts"]}
        for role, filename in (("reactions", "reactions.csv"), ("schema", "schema.json"), ("checksums", "checksums.csv")):
            item = metadata_artifacts.get(role)
            if item is None or item["sha256"] != sha256(package_dir / filename) or item["size_bytes"] != (package_dir / filename).stat().st_size:
                raise ValueError(f"metadata artifact hash mismatch in {slug}/{filename}")
        csv_result = validate_csv(package_dir / "reactions.csv", expected_members, expected_rows)
        reaction_hash = sha256(package_dir / "reactions.csv")
        if control_by_slug:
            control = control_by_slug[slug]
            if control["row_count"] != expected_rows or control["reaction_sha256"] != reaction_hash or control["metadata_sha256"] != sha256(package_dir / "metadata.json") or control["source_links_sha256"] != sha256(package_dir / "source-links.json") or control["checksums_sha256"] != sha256(package_dir / "checksums.csv"):
                raise ValueError(f"control manifest hash mismatch in {slug}")
        results.append({"dataset_slug": slug, "logical_dataset_id": logical_id, "row_count": csv_result["row_count"], "physical_source_count": len(expected_members), "reaction_sha256": reaction_hash, "reaction_size_bytes": (package_dir / "reactions.csv").stat().st_size, "remaining_literal_email_values": csv_result["remaining_literal_email_values"]})
        total_rows += csv_result["row_count"]
    if total_rows != expected_reaction_count:
        raise ValueError("aggregate reaction count does not match the frozen baseline")
    return {"schema_version": "1.0.0", "step_id": "step-12", "status": "complete", "input_hashes": {"semantic_name_map": sha256(semantic_map_path), "logical_dataset_members": sha256(members_path), "source_files_manifest": sha256(source_files_path), "control_manifest": control_hash}, "corpus_count": len(results), "physical_source_count": expected_physical_count, "reaction_count": total_rows, "orphan_physical_sources": 0, "duplicate_logical_memberships": 0, "unpinned_main_urls": 0, "remaining_literal_email_values": 0, "packages": results}


def write_reports(summary: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    for path in (json_path, markdown_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite validation report: {path}")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(
        "# Corpus staging validation\n\n"
        f"- Status: `{summary['status']}`\n"
        f"- Corpus packages: {summary['corpus_count']}\n"
        f"- Physical sources: {summary['physical_source_count']}\n"
        f"- Reactions: {summary['reaction_count']}\n"
        f"- Orphan physical sources: {summary['orphan_physical_sources']}\n"
        f"- Duplicate logical memberships: {summary['duplicate_logical_memberships']}\n"
        f"- Unpinned `/blob/main/` source URLs: {summary['unpinned_main_urls']}\n"
        f"- Remaining literal email values: {summary['remaining_literal_email_values']}\n\n"
        "The JSON companion contains per-corpus counts and hashes. It contains no reaction payload or matched sensitive value.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-root", required=True, type=Path)
    parser.add_argument("--semantic-map", required=True, type=Path)
    parser.add_argument("--members", required=True, type=Path)
    parser.add_argument("--source-files", required=True, type=Path)
    parser.add_argument("--schema-dir", required=True, type=Path)
    parser.add_argument("--control-manifest", type=Path)
    parser.add_argument("--json-report", required=True, type=Path)
    parser.add_argument("--markdown-report", required=True, type=Path)
    args = parser.parse_args()
    summary = validate(args.staging_root, args.semantic_map, args.members, args.source_files, args.schema_dir, args.control_manifest)
    write_reports(summary, args.json_report, args.markdown_report)
    print(json.dumps({key: summary[key] for key in ("corpus_count", "physical_source_count", "reaction_count")}, sort_keys=True))


if __name__ == "__main__":
    main()
