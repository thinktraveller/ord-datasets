#!/usr/bin/env python3
"""Assemble an atomic local RC containing only the 19 model-ready targets.

The builder deliberately writes a self-contained release tree outside the
repository's published ``datasets/`` view.  It never promotes a corpus,
original Parquet, or ``_needs_review`` object, and it refuses to overwrite an
existing candidate.  A later owner-authorized transport step may choose to
upload this exact tree after the preview validator accepts it.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

VERSION = "1.0.0"
PREVIEW_DIR = Path("provenance/model-ready-preview")
PAYLOAD_FILES = (
    "audit.jsonl",
    "checksums.csv",
    "dataset.csv",
    "exclusions.csv",
    "metadata.json",
    "row-map.csv",
    "schema.json",
    "source-links.json",
    "target-build-provenance.json",
    "yonod-config.json",
)
CHECKSUM_FILES = {
    "audit": "audit.jsonl",
    "dataset": "dataset.csv",
    "exclusions": "exclusions.csv",
    "row-map": "row-map.csv",
    "schema": "schema.json",
    "source-links": "source-links.json",
    "target-build-provenance": "target-build-provenance.json",
    "yonod-config": "yonod-config.json",
}
INVENTORY_HEADER = [
    "artifact_id",
    "target_slug",
    "target_id",
    "role",
    "artifact_path",
    "size_bytes",
    "sha256",
    "artifact_class",
    "disposition",
    "license_id",
    "redistribution_status",
    "origin",
    "source_artifact_ids_json",
]
CATALOG_HEADER = [
    "record_type",
    "dataset_slug",
    "display_name_en",
    "display_name_zh",
    "logical_dataset_id",
    "physical_dataset_ids_json",
    "physical_source_files_json",
    "target_id",
    "label_type",
    "label_unit",
    "readiness_status",
    "artifact_status",
    "license_id",
    "row_count",
    "content_sha256",
    "release_path",
    "metadata_path",
    "source_links_path",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, header: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_array(row: dict[str, str], field: str) -> list[str]:
    value = json.loads(row[field])
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a non-empty JSON string array")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} contains duplicate values")
    return value


def artifact_id(kind: str, value: str) -> str:
    return f"release-artifact-{kind}-{value.replace('_', '-') }"


def root_hash(root: Path, excluded: set[Path]) -> str:
    records: list[str] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if relative in excluded:
            continue
        records.append(f"{relative.as_posix()}\t{path.stat().st_size}\t{sha256(path)}")
    return hashlib.sha256(("\n".join(records) + "\n").encode("utf-8")).hexdigest()


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)


def validate_staging(
    staging_root: Path,
    target_map: list[dict[str, str]],
    target_control: dict[str, Any],
    source_by_id: dict[str, dict[str, str]],
    metadata_validator: Draft202012Validator,
    links_validator: Draft202012Validator,
) -> list[dict[str, Any]]:
    if target_control.get("status") != "staging_complete_not_released":
        raise ValueError("target control manifest is not a non-released staging manifest")
    control_by_slug = {item["target_slug"]: item for item in target_control.get("packages", [])}
    target_by_slug = {item["target_slug"]: item for item in target_map}
    if len(target_map) != 19 or len(target_by_slug) != 19 or set(control_by_slug) != set(target_by_slug):
        raise ValueError("preview must start with exactly the 19 frozen target packages")
    actual = {path.name for path in staging_root.iterdir() if path.is_dir()}
    if actual != set(target_by_slug) or list(staging_root.glob(".*.partial")):
        raise ValueError("staging target directories are incomplete or contain partial outputs")

    validated: list[dict[str, Any]] = []
    for slug in sorted(target_by_slug):
        target = target_by_slug[slug]
        control = control_by_slug[slug]
        directory = staging_root / slug
        files = {path.name for path in directory.iterdir() if path.is_file()}
        if files != set(PAYLOAD_FILES):
            raise ValueError(f"unexpected payload file set for {slug}")
        metadata = read_json(directory / "metadata.json")
        source_links = read_json(directory / "source-links.json")
        metadata_validator.validate(metadata)
        links_validator.validate(source_links)
        physical_ids = parse_array(target, "physical_dataset_ids_json")
        physical_files = parse_array(target, "physical_source_files_json")
        if (
            metadata["dataset_kind"] != "model-ready"
            or metadata["dataset_slug"] != slug
            or metadata["target_id"] != target["target_id"]
            or metadata["logical_dataset_id"] != target["logical_dataset_id"]
            or metadata["physical_dataset_ids"] != physical_ids
            or metadata["readiness_status"] != target["readiness_status"]
            or metadata["artifact_status"] != "staged"
            or metadata["label"]["type"] != target["label_type"]
            or metadata["label"]["unit"] != target["label_unit"]
            or metadata["label"]["column"] != target["label_column"]
        ):
            raise ValueError(f"metadata does not match frozen target mapping: {slug}")
        if (
            control["target_id"] != target["target_id"]
            or control["logical_dataset_id"] != target["logical_dataset_id"]
            or control["readiness_status"] != target["readiness_status"]
            or int(control["included_count"]) != int(target["included_count"])
            or int(control["excluded_count"]) != int(target["excluded_count"])
        ):
            raise ValueError(f"target control record does not match frozen map: {slug}")
        expected_links = list(zip(physical_ids, physical_files, strict=True))
        actual_links = [(item["physical_dataset_id"], item["source_file"]) for item in source_links["links"]]
        if actual_links != expected_links:
            raise ValueError(f"source links do not match frozen target map: {slug}")
        for link in source_links["links"]:
            frozen = source_by_id.get(link["physical_dataset_id"])
            if frozen is None:
                raise ValueError(f"unknown physical source in {slug}")
            for link_field, manifest_field in (
                ("source_file", "upstream_path"),
                ("upstream_revision", "upstream_revision"),
                ("source_file_url", "source_file_url"),
                ("source_sha256", "source_sha256"),
                ("git_lfs_oid", "git_lfs_oid"),
                ("data_license_id", "data_license_id"),
            ):
                if link[link_field] != frozen[manifest_field]:
                    raise ValueError(f"source-link field differs from frozen source manifest: {slug}/{link_field}")
        checksum_rows = {row["role"]: row for row in read_csv(directory / "checksums.csv")}
        if set(checksum_rows) != set(CHECKSUM_FILES):
            raise ValueError(f"unexpected checksums roles for {slug}")
        for role, filename in CHECKSUM_FILES.items():
            path = directory / filename
            row = checksum_rows[role]
            if row["path"] != filename or row["sha256"] != sha256(path) or int(row["size_bytes"]) != path.stat().st_size:
                raise ValueError(f"checksums.csv disagrees with payload: {slug}/{filename}")
        for filename, expected in control["artifacts"].items():
            path = directory / filename
            if not path.is_file() or sha256(path) != expected["sha256"] or path.stat().st_size != expected["size_bytes"]:
                raise ValueError(f"control manifest disagrees with staging payload: {slug}/{filename}")
        validated.append({"target": target, "control": control, "metadata": metadata, "source_links": source_links})
    return validated


def write_preview_documents(root: Path, release_id: str, counts: dict[str, int], status_counts: Counter[str]) -> None:
    status_lines = "\n".join(f"- `{status}`: {count}" for status, count in sorted(status_counts.items()))
    (root / "README.md").write_text(
        "# ord-datasets model-ready preview\n\n"
        f"`{release_id}` is a local, model-ready-only preview release candidate. It contains {counts['model_ready_targets']} target packages from {counts['model_ready_packages']} packages: {counts['target_payload_files']} payload files totaling {counts['target_payload_bytes']} bytes.\n\n"
        "It is not a complete ORD corpus release and not an accepted benchmark. The 41 corpus payloads, all original ORD Parquet payloads, and all `_needs_review` payloads are explicitly excluded. Corpus identities in lineage are reference-only and are not downloadable payloads.\n\n"
        "Every target includes its dataset, schema, configuration, row map, audit, exclusions, immutable source links, build provenance, metadata, and checksums. Verify the release with `provenance/model-ready-preview/release-manifest.json`, `provenance/model-ready-preview/artifact-inventory.csv`, and each target's `checksums.csv`.\n\n"
        "## Readiness status\n\n"
        "The statuses below are preserved from staging and do not imply benchmark acceptance:\n\n"
        f"{status_lines}\n",
        encoding="utf-8",
    )
    (root / "DATA_CARD.md").write_text(
        "# Model-ready preview data card\n\n"
        "This release candidate packages task-specific projections derived from ORD, rather than a complete reaction corpus. Each target retains the source-defined label type and unit, included/excluded decisions, audit trail, and two-hop lineage through a reference-only logical corpus identity to a revision-pinned ORD source file.\n\n"
        "Data and data-derived metadata are offered under CC BY-SA 4.0. The accompanying build and validation code is Apache-2.0. See `NOTICE`, `LICENSE-DATA`, and `LICENSE-CODE`. The original ORD Parquet files are not redistributed here; `source-links.json` and `provenance/source-files.initial.csv` provide immutable source identities, hashes, LFS OIDs, and commit-pinned URLs.\n\n"
        "Known target readiness statuses are retained verbatim in `datasets/catalog.csv` and each `metadata.json`. In particular, partial, research-only, source-caveat, adapter-blocked, and campaign-evaluation-pending targets must not be presented as accepted benchmarks.\n",
        encoding="utf-8",
    )
    (root / "CITATION.cff").write_text(
        "cff-version: 1.2.0\n"
        "message: \"If you use this work, please cite this preview and the Open Reaction Database.\"\n"
        "title: \"ord-datasets model-ready preview\"\n"
        f"version: \"{release_id.removeprefix('v')}\"\n"
        "date-released: \"2026-09-12\"\n"
        "license: \"CC-BY-SA-4.0\"\n"
        "authors:\n"
        "  - name: \"ord-datasets contributors\"\n"
        "references:\n"
        "  - type: software\n"
        "    title: \"Open Reaction Database\"\n"
        "    url: \"https://github.com/open-reaction-database/ord-data/tree/83f971f586f6ad18f358ae4ae99d045e94ed2066\"\n"
        "    license: \"CC-BY-SA-4.0\"\n",
        encoding="utf-8",
    )
    (root / "NOTICE").write_text(
        "ord-datasets model-ready preview NOTICE\n"
        "=======================================\n\n"
        "The data and data-derived metadata in this preview are adaptations of the Open Reaction Database Project (ORD) and are offered under Creative Commons Attribution-ShareAlike 4.0 International. Reuse must provide attribution, link to the source and license, identify modifications, and comply with ShareAlike.\n\n"
        "This preview redistributes no ORD Parquet payload, corpus payload, or `_needs_review` payload. Commit-pinned ORD source URLs, content hashes, and Git LFS OIDs are preserved as provenance metadata only.\n\n"
        "Code is separately licensed under Apache-2.0. No license here grants rights to material outside this declared preview scope.\n",
        encoding="utf-8",
    )


def build(
    staging_root: Path,
    target_map_path: Path,
    target_control_path: Path,
    source_files_path: Path,
    schema_dir: Path,
    project_root: Path,
    release_root: Path,
    release_id: str,
    project_commit: str,
    build_timestamp: str,
    report_path: Path,
) -> dict[str, Any]:
    for path in (staging_root, target_map_path, target_control_path, source_files_path, project_root / "LICENSE-DATA", project_root / "LICENSE-CODE"):
        if path == staging_root:
            if not path.is_dir():
                raise NotADirectoryError(path)
        else:
            require_file(path)
    if release_root.exists() or report_path.exists():
        raise FileExistsError("release root or build report already exists; refusing to overwrite an RC")
    if not release_id.startswith("v") or "-model-ready-preview" not in release_id:
        raise ValueError("release ID must name the model-ready-preview track")
    if len(project_commit) != 40 or any(char not in "0123456789abcdef" for char in project_commit):
        raise ValueError("project commit must be a 40-character lowercase SHA-1")

    target_map = read_csv(target_map_path)
    source_rows = read_csv(source_files_path)
    source_by_id = {row["physical_dataset_id"]: row for row in source_rows}
    if len(source_rows) != 53 or len(source_by_id) != 53:
        raise ValueError("preview source closure must use the frozen 53-source manifest")
    target_control = read_json(target_control_path)
    metadata_validator = Draft202012Validator(read_json(schema_dir / "dataset-metadata.schema.json"))
    links_validator = Draft202012Validator(read_json(schema_dir / "source-links.schema.json"))
    preview_manifest_validator = Draft202012Validator(read_json(schema_dir / "model-ready-preview-release-manifest.schema.json"))
    catalog_validator = Draft202012Validator(read_json(schema_dir / "catalog-record.schema.json"))
    artifact_validator = Draft202012Validator(read_json(schema_dir / "artifact-record.schema.json"))
    transformation_validator = Draft202012Validator(read_json(schema_dir / "transformation-record.schema.json"))
    packages = validate_staging(staging_root, target_map, target_control, source_by_id, metadata_validator, links_validator)

    release_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = release_root.parent / f".{release_root.name}.{uuid.uuid4().hex}.partial"
    temporary.mkdir()
    try:
        payload_inventory: list[dict[str, Any]] = []
        catalog_csv: list[dict[str, str]] = []
        catalog_json: list[dict[str, Any]] = []
        target_nodes: dict[str, str] = {}
        corpus_nodes: dict[str, str] = {}
        source_nodes: dict[str, str] = {}
        logical_sources: dict[str, set[str]] = {}
        status_counts: Counter[str] = Counter()
        for item in packages:
            target, control, source_links = item["target"], item["control"], item["source_links"]
            slug, target_id, logical_id = target["target_slug"], target["target_id"], target["logical_dataset_id"]
            destination = temporary / "datasets" / "model-ready" / slug
            destination.mkdir(parents=True)
            for filename in PAYLOAD_FILES:
                source = staging_root / slug / filename
                copied = destination / filename
                shutil.copyfile(source, copied)
                if source.stat().st_size != copied.stat().st_size or sha256(source) != sha256(copied):
                    raise ValueError(f"payload copy mismatch: {slug}/{filename}")
                role = filename.removesuffix(".json").removesuffix(".csv").removesuffix(".jsonl")
                target_node = artifact_id("target", slug)
                payload_inventory.append(
                    {
                        "artifact_id": f"{target_node}-{role.replace('_', '-')}",
                        "target_slug": slug,
                        "target_id": target_id,
                        "role": role,
                        "artifact_path": copied.relative_to(temporary).as_posix(),
                        "size_bytes": copied.stat().st_size,
                        "sha256": sha256(copied),
                        "artifact_class": "model-ready",
                        "disposition": "staged",
                        "license_id": "CC-BY-SA-4.0",
                        "redistribution_status": "pending",
                        "origin": "step-13-model-ready-staging",
                        "source_artifact_ids_json": json.dumps([target_node]),
                    }
                )
            dataset_path = destination / "dataset.csv"
            catalog_row = {
                "record_type": "model-ready",
                "dataset_slug": slug,
                "display_name_en": target["display_name_en"],
                "display_name_zh": target["display_name_zh"],
                "logical_dataset_id": logical_id,
                "physical_dataset_ids_json": target["physical_dataset_ids_json"],
                "physical_source_files_json": target["physical_source_files_json"],
                "target_id": target_id,
                "label_type": target["label_type"],
                "label_unit": target["label_unit"],
                "readiness_status": target["readiness_status"],
                "artifact_status": "staged",
                "license_id": "CC-BY-SA-4.0",
                "row_count": str(control["included_count"]),
                "content_sha256": sha256(dataset_path),
                "release_path": f"datasets/model-ready/{slug}",
                "metadata_path": f"datasets/model-ready/{slug}/metadata.json",
                "source_links_path": f"datasets/model-ready/{slug}/source-links.json",
            }
            catalog_instance = {
                "schema_version": VERSION,
                **{key: value for key, value in catalog_row.items() if key not in {"physical_dataset_ids_json", "physical_source_files_json", "row_count"}},
                "physical_dataset_ids": json.loads(catalog_row.pop("physical_dataset_ids_json")),
                "physical_source_files": json.loads(catalog_row.pop("physical_source_files_json")),
                "row_count": int(catalog_row["row_count"]),
            }
            catalog_row["physical_dataset_ids_json"] = json.dumps(catalog_instance["physical_dataset_ids"], ensure_ascii=False)
            catalog_row["physical_source_files_json"] = json.dumps(catalog_instance["physical_source_files"], ensure_ascii=False)
            catalog_validator.validate(catalog_instance)
            catalog_csv.append(catalog_row)
            catalog_json.append(catalog_instance)
            target_nodes[slug] = artifact_id("target", slug)
            corpus_slug = target["corpus_directory_slug"]
            corpus_nodes[logical_id] = artifact_id("corpus-reference", corpus_slug)
            logical_sources.setdefault(logical_id, set())
            for link in source_links["links"]:
                physical_id = link["physical_dataset_id"]
                source_nodes[physical_id] = artifact_id("source", physical_id.removeprefix("ord_dataset-"))
                logical_sources[logical_id].add(physical_id)
            status_counts[target["readiness_status"]] += 1

        catalog_csv.sort(key=lambda row: row["dataset_slug"])
        catalog_json.sort(key=lambda row: row["dataset_slug"])
        write_csv(temporary / "datasets" / "catalog.csv", CATALOG_HEADER, catalog_csv)
        write_json(temporary / "datasets" / "catalog.json", catalog_json)
        preview_provenance = temporary / PREVIEW_DIR
        write_csv(preview_provenance / "artifact-inventory.csv", INVENTORY_HEADER, sorted(payload_inventory, key=lambda row: row["artifact_path"]))
        safe_copy = lambda source, destination: shutil.copyfile(source, destination)
        (temporary / "provenance").mkdir(exist_ok=True)
        safe_copy(source_files_path, temporary / "provenance" / "source-files.initial.csv")
        safe_copy(target_map_path, temporary / "provenance" / "semantic-target-map.csv")
        safe_copy(project_root / "LICENSE-DATA", temporary / "LICENSE-DATA")
        safe_copy(project_root / "LICENSE-CODE", temporary / "LICENSE-CODE")

        artifact_nodes: list[dict[str, Any]] = []
        for physical_id in sorted(source_nodes):
            source = source_by_id[physical_id]
            artifact_nodes.append(
                {
                    "schema_version": VERSION,
                    "artifact_id": source_nodes[physical_id],
                    "artifact_path": source["upstream_path"],
                    "object_type": "virtual_object",
                    "size_bytes": int(source["size_bytes"]),
                    "sha256": source["source_sha256"],
                    "artifact_class": "source",
                    "disposition": "manifest_only",
                    "license_id": "CC-BY-SA-4.0",
                    "redistribution_status": "not_applicable",
                    "origin": source["source_file_url"],
                    "source_artifact_ids": [],
                }
            )
        for logical_id in sorted(corpus_nodes):
            artifact_nodes.append(
                {
                    "schema_version": VERSION,
                    "artifact_id": corpus_nodes[logical_id],
                    "artifact_path": f"provenance/model-ready-preview/reference-only-corpus/{corpus_nodes[logical_id].removeprefix('release-artifact-corpus-reference-')}",
                    "object_type": "virtual_object",
                    "size_bytes": 0,
                    "sha256": None,
                    "artifact_class": "corpus",
                    "disposition": "manifest_only",
                    "license_id": "CC-BY-SA-4.0",
                    "redistribution_status": "not_applicable",
                    "origin": "reference-only logical corpus identity; corpus payload excluded from model-ready preview",
                    "source_artifact_ids": sorted(source_nodes[item] for item in logical_sources[logical_id]),
                }
            )
        for item in packages:
            target, control = item["target"], item["control"]
            slug = target["target_slug"]
            artifact_nodes.append(
                {
                    "schema_version": VERSION,
                    "artifact_id": target_nodes[slug],
                    "artifact_path": f"datasets/model-ready/{slug}/dataset.csv",
                    "object_type": "file",
                    "size_bytes": int(control["artifacts"]["dataset.csv"]["size_bytes"]),
                    "sha256": control["artifacts"]["dataset.csv"]["sha256"],
                    "artifact_class": "model-ready",
                    "disposition": "staged",
                    "license_id": "CC-BY-SA-4.0",
                    "redistribution_status": "pending",
                    "origin": "step-13-model-ready-staging",
                    "source_artifact_ids": [corpus_nodes[target["logical_dataset_id"]]],
                }
            )
        for node in artifact_nodes:
            artifact_validator.validate(node)
        with (preview_provenance / "release-artifacts.jsonl").open("w", encoding="utf-8") as handle:
            for node in sorted(artifact_nodes, key=lambda item: item["artifact_id"]):
                handle.write(json.dumps(node, ensure_ascii=False, sort_keys=True) + "\n")

        edge_rows: list[dict[str, str]] = []
        for index, (logical_id, physical_id) in enumerate(
            sorted((logical, physical) for logical, physical_ids in logical_sources.items() for physical in physical_ids), 1
        ):
            edge_rows.append(
                {
                    "edge_id": f"edge-preview-source-reference-{index}",
                    "from_artifact_id": source_nodes[physical_id],
                    "to_artifact_id": corpus_nodes[logical_id],
                    "transformation_id": "transform-model-ready-preview-rc",
                    "relationship": "derived_from",
                    "status": "complete",
                }
            )
        for index, item in enumerate(sorted(packages, key=lambda item: item["target"]["target_slug"]), 1):
            target = item["target"]
            edge_rows.append(
                {
                    "edge_id": f"edge-preview-reference-target-{index}",
                    "from_artifact_id": corpus_nodes[target["logical_dataset_id"]],
                    "to_artifact_id": target_nodes[target["target_slug"]],
                    "transformation_id": "transform-model-ready-preview-rc",
                    "relationship": "projects",
                    "status": "complete",
                }
            )
        write_csv(preview_provenance / "lineage-edges.csv", ["edge_id", "from_artifact_id", "to_artifact_id", "transformation_id", "relationship", "status"], edge_rows)
        transformation = {
            "schema_version": VERSION,
            "transformation_id": "transform-model-ready-preview-rc",
            "step_id": "step-26",
            "tool": "build_model_ready_preview_rc.py",
            "pipeline_commit": project_commit,
            "command": "python pipeline/scripts/build_model_ready_preview_rc.py --staging-root <staging-root> --release-root <release-root>",
            "config_sha256": sha256(target_map_path),
            "input_artifact_ids": sorted([*source_nodes.values(), *corpus_nodes.values()]),
            "output_artifact_ids": sorted(target_nodes.values()),
            "started_at": build_timestamp,
            "ended_at": build_timestamp,
            "status": "complete",
            "error_code": None,
        }
        transformation_validator.validate(transformation)
        with (preview_provenance / "transformations.jsonl").open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(transformation, ensure_ascii=False, sort_keys=True) + "\n")

        counts = {
            "physical_sources_referenced": len(source_nodes),
            "logical_corpus_references": len(corpus_nodes),
            "model_ready_packages": len(corpus_nodes),
            "model_ready_targets": len(packages),
            "target_payload_files": len(payload_inventory),
            "target_payload_bytes": sum(int(item["size_bytes"]) for item in payload_inventory),
            "largest_target_file_bytes": max(int(item["size_bytes"]) for item in payload_inventory),
        }
        if counts["model_ready_packages"] != 15 or counts["model_ready_targets"] != 19 or counts["target_payload_files"] != 190:
            raise ValueError("preview candidate does not meet the frozen 15/19/190 scope")
        write_preview_documents(temporary, release_id, counts, status_counts)
        manifest_relative = PREVIEW_DIR / "release-manifest.json"
        manifest = {
            "schema_version": VERSION,
            "release_id": release_id,
            "release_status": "local-release-candidate",
            "release_track": "model-ready-preview",
            "project_commit": project_commit,
            "ord_upstream_revision": source_rows[0]["upstream_revision"],
            "source_manifest_path": "provenance/source-files.initial.csv",
            "source_manifest_sha256": sha256(temporary / "provenance" / "source-files.initial.csv"),
            "contract_versions": {"catalog": VERSION, "metadata": VERSION, "source_links": VERSION, "artifact_inventory": VERSION, "transformation": VERSION, "release_manifest": VERSION, "csv_contracts": "1.1.0"},
            "counts": counts,
            "excluded_payloads": ["datasets/corpus payload", "original ORD Parquet payload", "_needs_review payload"],
            "license": {"data_license_id": "CC-BY-SA-4.0", "code_license_id": "Apache-2.0", "notice_path": "NOTICE"},
            "catalog_path": "datasets/catalog.csv",
            "artifact_inventory_path": "provenance/model-ready-preview/artifact-inventory.csv",
            "release_artifacts_path": "provenance/model-ready-preview/release-artifacts.jsonl",
            "transformations_path": "provenance/model-ready-preview/transformations.jsonl",
            "lineage_edges_path": "provenance/model-ready-preview/lineage-edges.csv",
            "root_hash_scope": "all preview tree files excluding provenance/model-ready-preview/release-manifest.json",
            "root_sha256": root_hash(temporary, {manifest_relative}),
        }
        preview_manifest_validator.validate(manifest)
        write_json(temporary / manifest_relative, manifest)
        banned = [
            path.relative_to(temporary).as_posix()
            for path in temporary.rglob("*")
            if path.is_file()
            and (
                path.suffix == ".parquet"
                or "_needs_review" in path.relative_to(temporary).parts
                or path.relative_to(temporary).as_posix().startswith("datasets/corpus/")
            )
        ]
        if banned:
            raise ValueError(f"preview candidate contains excluded payload paths: {banned}")
        if root_hash(temporary, {manifest_relative}) != manifest["root_sha256"]:
            raise ValueError("preview root hash changed before promotion")
        os.replace(temporary, release_root)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise

    result = {
        "schema_version": VERSION,
        "step_id": "step-26-preview",
        "status": "local_rc_built_pending_pilot_and_owner_go",
        "release_id": release_id,
        "release_track": "model-ready-preview",
        "project_commit": project_commit,
        "payload": counts,
        "readiness_status_counts": dict(sorted(status_counts.items())),
        "excluded_payloads": manifest["excluded_payloads"],
        "lineage": {"nodes": len(artifact_nodes), "edges": len(edge_rows), "reference_only_corpus_nodes": len(corpus_nodes)},
        "release_manifest_sha256": sha256(release_root / manifest_relative),
        "root_sha256": manifest["root_sha256"],
        "atomic_promotion": True,
        "remote_write_attempted": False,
        "remaining_blockers": ["owner_transport_pilot", "owner_release_go_and_remote_write_authorization"],
    }
    write_json(report_path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-root", required=True, type=Path)
    parser.add_argument("--target-map", required=True, type=Path)
    parser.add_argument("--target-control", required=True, type=Path)
    parser.add_argument("--source-files", required=True, type=Path)
    parser.add_argument("--schema-dir", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--release-root", required=True, type=Path)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--project-commit", required=True)
    parser.add_argument("--build-timestamp", default="2026-09-12T00:00:00Z")
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                staging_root=args.staging_root,
                target_map_path=args.target_map,
                target_control_path=args.target_control,
                source_files_path=args.source_files,
                schema_dir=args.schema_dir,
                project_root=args.project_root,
                release_root=args.release_root,
                release_id=args.release_id,
                project_commit=args.project_commit,
                build_timestamp=args.build_timestamp,
                report_path=args.report,
            ),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
