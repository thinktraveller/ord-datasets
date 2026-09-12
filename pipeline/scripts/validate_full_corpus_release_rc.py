#!/usr/bin/env python3
"""Validate a local full-corpus release candidate without remote writes."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_full_corpus_release_rc import (
    CATALOG_HEADER,
    EDGE_HEADER,
    FROZEN,
    INVENTORY_HEADER,
    MANIFEST_RELATIVE,
    PAYLOAD_FILES,
    RELEASE_DIR,
    parse_sha256sums,
    root_hash,
    sha256,
)
from validate_corpus_staging import validate as validate_corpus_staging


VERSION = "1.0.0"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[str] | None, list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def schema_validator(schema_dir: Path, name: str) -> Draft202012Validator:
    return Draft202012Validator(read_json(schema_dir / name))


def expected_tree_paths(semantic_rows: list[dict[str, str]]) -> set[str]:
    paths = {
        "README.md", "LICENSE-DATA", "LICENSE-CODE", "NOTICE", "CITATION.cff", "SHA256SUMS",
        "datasets/catalog.csv", "datasets/catalog.json", "provenance/source-files.initial.csv",
        "provenance/source-files.csv", "provenance/semantic-name-map.csv", "provenance/logical-dataset-members.csv",
        "provenance/full-corpus-release/artifact-inventory.csv",
        "provenance/full-corpus-release/release-artifacts.jsonl",
        "provenance/full-corpus-release/lineage-edges.csv",
        "provenance/full-corpus-release/transformations.jsonl",
        "provenance/full-corpus-release/staging-control-manifest.json",
        "provenance/full-corpus-release/private-transport-SHA256SUMS",
        "provenance/full-corpus-release/release-manifest.json",
    }
    for row in semantic_rows:
        paths.update(f"datasets/corpus/{row['directory_slug']}/{name}" for name in PAYLOAD_FILES)
    return paths


def validate(
    release_root: Path,
    schema_dir: Path,
    release_decision_path: Path | None = None,
    strict_frozen_baseline: bool = True,
) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[dict[str, Any]] = []
    manifest: dict[str, Any] = {}
    semantic_rows: list[dict[str, str]] = []
    expected_counts = dict(FROZEN)
    if not release_root.is_dir():
        return {
            "schema_version": VERSION, "step_id": "step-32-full-corpus-rc-validation", "status": "rejected",
            "blocking_check_failures": 1, "blocking_checks": [f"release root is not a directory: {release_root}"],
            "owner_gates": [], "remote_write_attempted": False,
        }
    try:
        manifest = read_json(release_root / MANIFEST_RELATIVE)
        schema_validator(schema_dir, "full-corpus-release-manifest.schema.json").validate(manifest)
        if not strict_frozen_baseline:
            expected_counts = dict(manifest["counts"])
        elif manifest.get("counts") != {**FROZEN, "largest_corpus_file_bytes": manifest.get("counts", {}).get("largest_corpus_file_bytes")}:
            add_failure(failures, "manifest counts differ from the frozen full-corpus baseline")
    except (OSError, ValueError, ValidationError, KeyError) as error:
        add_failure(failures, f"cannot load or validate full-corpus manifest: {error}")

    for name in ("dataset-metadata.schema.json", "source-links.schema.json", "catalog-record.schema.json", "artifact-record.schema.json", "transformation-record.schema.json"):
        try:
            schema_validator(schema_dir, name)
        except (OSError, ValueError, ValidationError) as error:
            add_failure(failures, f"cannot load schema {name}: {error}")

    source_path = release_root / "provenance/source-files.initial.csv"
    semantic_path = release_root / "provenance/semantic-name-map.csv"
    members_path = release_root / "provenance/logical-dataset-members.csv"
    control_path = release_root / RELEASE_DIR / "staging-control-manifest.json"
    try:
        _, semantic_rows = read_csv(semantic_path)
        source_header, source_rows = read_csv(source_path)
        _, duplicate_source_rows = read_csv(release_root / "provenance/source-files.csv")
        _, member_rows = read_csv(members_path)
        if source_rows != duplicate_source_rows:
            add_failure(failures, "source-files.csv and source-files.initial.csv are not byte-equivalent records")
        expected_hashes = {
            "source_manifest_sha256": source_path,
            "semantic_map_sha256": semantic_path,
            "members_sha256": members_path,
            "staging_control_manifest_sha256": control_path,
        }
        for field, path in expected_hashes.items():
            if manifest.get(field) != sha256(path):
                add_failure(failures, f"manifest {field} does not match {path.relative_to(release_root)}")
        if not source_header or len(source_rows) != expected_counts["physical_sources_referenced"]:
            add_failure(failures, "source manifest count differs from candidate scope")
        if len(semantic_rows) != expected_counts["corpus_packages"]:
            add_failure(failures, "semantic corpus count differs from candidate scope")
        if len(member_rows) != expected_counts["physical_sources_referenced"]:
            add_failure(failures, "logical member count differs from candidate scope")
        expected_files = expected_tree_paths(semantic_rows)
        actual_files = {path.relative_to(release_root).as_posix() for path in release_root.rglob("*") if path.is_file()}
        if actual_files != expected_files:
            unexpected = sorted(actual_files - expected_files)
            missing = sorted(expected_files - actual_files)
            add_failure(failures, f"candidate tree violates the exact public scope; unexpected={unexpected[:5]}, missing={missing[:5]}")
        banned_paths = [path for path in actual_files if path.endswith(".parquet") or "_needs_review" in path or "/model-ready/" in path or "/.git/" in path]
        if banned_paths:
            add_failure(failures, f"candidate tree contains excluded path(s): {banned_paths[:5]}")
    except (OSError, csv.Error, KeyError, TypeError) as error:
        source_rows = member_rows = []
        add_failure(failures, f"cannot validate candidate provenance closure: {error}")

    staging_summary: dict[str, Any] = {}
    try:
        staging_summary = validate_corpus_staging(
            release_root / "datasets/corpus", semantic_path, members_path, source_path, schema_dir, control_path,
            expected_corpus_count=expected_counts["corpus_packages"],
            expected_physical_count=expected_counts["physical_sources_referenced"],
            expected_reaction_count=expected_counts["reactions"],
        )
    except (OSError, ValueError, ValidationError, csv.Error, KeyError, TypeError) as error:
        add_failure(failures, f"corpus payload validation failed: {error}")

    payload_paths = sorted((release_root / "datasets/corpus").glob("*/*")) if (release_root / "datasets/corpus").is_dir() else []
    payload_paths = [path for path in payload_paths if path.is_file()]
    payload_bytes = sum(path.stat().st_size for path in payload_paths)
    largest_payload = max((path.stat().st_size for path in payload_paths), default=0)
    try:
        candidate_entries = parse_sha256sums(release_root / "SHA256SUMS", package_prefix="./datasets/corpus/")
        actual_entries = {f"./{path.relative_to(release_root).as_posix()}": sha256(path) for path in payload_paths}
        if candidate_entries != actual_entries:
            add_failure(failures, "candidate SHA256SUMS is not the exact corpus payload closure")
        if manifest.get("sha256sums_sha256") != sha256(release_root / "SHA256SUMS"):
            add_failure(failures, "manifest SHA256SUMS hash does not match the candidate file")
        private_path = release_root / RELEASE_DIR / "private-transport-SHA256SUMS"
        private_entries = parse_sha256sums(private_path, package_prefix="./")
        mapped_private_entries = {f"./datasets/corpus/{name.removeprefix('./')}": digest for name, digest in private_entries.items()}
        if candidate_entries != mapped_private_entries:
            add_failure(failures, "candidate payload hashes differ from the private-transport snapshot")
        if manifest.get("private_transport_sha256sums_sha256") != sha256(private_path):
            add_failure(failures, "manifest private-transport SHA256SUMS hash does not match")
    except (OSError, ValueError) as error:
        add_failure(failures, f"cannot validate candidate and private SHA256SUMS: {error}")

    metadata_validator = schema_validator(schema_dir, "dataset-metadata.schema.json")
    links_validator = schema_validator(schema_dir, "source-links.schema.json")
    catalog_validator = schema_validator(schema_dir, "catalog-record.schema.json")
    catalog_by_slug: dict[str, dict[str, str]] = {}
    try:
        header, catalog_rows = read_csv(release_root / "datasets/catalog.csv")
        if header != CATALOG_HEADER:
            add_failure(failures, "corpus catalog header differs from contract")
        catalog_by_slug = {row["dataset_slug"]: row for row in catalog_rows}
        expected_slugs = {row["directory_slug"] for row in semantic_rows}
        if len(catalog_rows) != expected_counts["corpus_packages"] or set(catalog_by_slug) != expected_slugs:
            add_failure(failures, "corpus catalog is not exactly the semantic corpus closure")
        catalog_json = read_json(release_root / "datasets/catalog.json")
        if not isinstance(catalog_json, list) or len(catalog_json) != len(catalog_rows):
            add_failure(failures, "catalog.json does not mirror catalog.csv")
        for semantic in semantic_rows:
            slug = semantic["directory_slug"]
            row = catalog_by_slug[slug]
            directory = release_root / "datasets/corpus" / slug
            metadata = read_json(directory / "metadata.json")
            links = read_json(directory / "source-links.json")
            metadata_validator.validate(metadata)
            links_validator.validate(links)
            instance = {
                "schema_version": VERSION, "record_type": row["record_type"], "dataset_slug": row["dataset_slug"],
                "display_name_en": row["display_name_en"], "display_name_zh": row["display_name_zh"] or None,
                "logical_dataset_id": row["logical_dataset_id"], "physical_dataset_ids": json.loads(row["physical_dataset_ids_json"]),
                "physical_source_files": json.loads(row["physical_source_files_json"]), "target_id": None,
                "label_type": None, "label_unit": None, "readiness_status": row["readiness_status"],
                "artifact_status": row["artifact_status"], "license_id": row["license_id"], "row_count": int(row["row_count"]),
                "content_sha256": row["content_sha256"], "release_path": row["release_path"],
                "metadata_path": row["metadata_path"], "source_links_path": row["source_links_path"],
            }
            catalog_validator.validate(instance)
            if (
                row["record_type"] != "corpus" or row["logical_dataset_id"] != semantic["logical_dataset_id"]
                or instance["physical_dataset_ids"] != json.loads(semantic["physical_dataset_ids_json"])
                or instance["physical_source_files"] != json.loads(semantic["physical_source_files_json"])
                or row["content_sha256"] != sha256(directory / "reactions.csv")
                or int(row["row_count"]) != metadata["corpus_row_count"]
                or row["artifact_status"] != metadata["artifact_status"]
            ):
                add_failure(failures, f"catalog or metadata identity mismatch: {slug}")
            linked = [(item["physical_dataset_id"], item["source_file"]) for item in links["links"]]
            if linked != list(zip(instance["physical_dataset_ids"], instance["physical_source_files"], strict=True)):
                add_failure(failures, f"catalog source closure differs from links: {slug}")
        json_by_slug = {item.get("dataset_slug"): item for item in catalog_json if isinstance(item, dict)}
        if set(json_by_slug) != set(catalog_by_slug):
            add_failure(failures, "catalog.json slug set differs from catalog.csv")
    except (OSError, ValueError, ValidationError, csv.Error, KeyError, TypeError) as error:
        add_failure(failures, f"cannot validate corpus catalog and package metadata: {error}")

    artifact_nodes: list[dict[str, Any]] = []
    edge_rows: list[dict[str, str]] = []
    try:
        header, inventory_rows = read_csv(release_root / RELEASE_DIR / "artifact-inventory.csv")
        if header != INVENTORY_HEADER:
            add_failure(failures, "corpus artifact-inventory header differs from contract")
        inventory_paths = {row["artifact_path"] for row in inventory_rows}
        actual_payload_paths = {path.relative_to(release_root).as_posix() for path in payload_paths}
        if len(inventory_rows) != expected_counts["corpus_payload_files"] or inventory_paths != actual_payload_paths:
            add_failure(failures, "artifact inventory is not the exact corpus payload closure")
        for row in inventory_rows:
            path = release_root / row["artifact_path"]
            if row["sha256"] != sha256(path) or int(row["size_bytes"]) != path.stat().st_size:
                add_failure(failures, f"artifact inventory hash mismatch: {row['artifact_path']}")
        artifact_validator = schema_validator(schema_dir, "artifact-record.schema.json")
        artifact_nodes = [json.loads(line) for line in (release_root / RELEASE_DIR / "release-artifacts.jsonl").read_text(encoding="utf-8").splitlines() if line]
        for node in artifact_nodes:
            artifact_validator.validate(node)
        node_by_id = {node["artifact_id"]: node for node in artifact_nodes}
        source_nodes = [node for node in artifact_nodes if node["artifact_class"] == "source"]
        corpus_nodes = [node for node in artifact_nodes if node["artifact_class"] == "corpus"]
        if len(node_by_id) != len(artifact_nodes) or len(source_nodes) != expected_counts["physical_sources_referenced"] or len(corpus_nodes) != expected_counts["corpus_packages"]:
            add_failure(failures, "release artifact lineage nodes do not match source/corpus closure")
        header, edge_rows = read_csv(release_root / RELEASE_DIR / "lineage-edges.csv")
        if header != EDGE_HEADER or len(edge_rows) != expected_counts["physical_sources_referenced"]:
            add_failure(failures, "lineage edge count or header differs from the physical-source closure")
        if any(row["status"] != "complete" or row["relationship"] != "derived_from" or row["from_artifact_id"] not in node_by_id or row["to_artifact_id"] not in node_by_id for row in edge_rows):
            add_failure(failures, "lineage edges are incomplete or reference unknown artifact nodes")
        transformation_validator = schema_validator(schema_dir, "transformation-record.schema.json")
        transformations = [json.loads(line) for line in (release_root / RELEASE_DIR / "transformations.jsonl").read_text(encoding="utf-8").splitlines() if line]
        if len(transformations) != 1:
            add_failure(failures, "candidate must contain exactly one corpus RC transformation")
        for transformation in transformations:
            transformation_validator.validate(transformation)
            if transformation["transformation_id"] != "transform-full-corpus-rc":
                add_failure(failures, "candidate transformation does not identify the full corpus RC")
    except (OSError, ValueError, ValidationError, csv.Error, KeyError, TypeError) as error:
        add_failure(failures, f"cannot validate candidate artifact inventory or lineage: {error}")

    actual_counts = {
        "physical_sources_referenced": len(source_rows), "corpus_packages": len(semantic_rows),
        "corpus_payload_files": len(payload_paths), "corpus_payload_bytes": payload_bytes,
        "reactions": staging_summary.get("reaction_count"), "largest_corpus_file_bytes": largest_payload,
    }
    if manifest.get("counts") != actual_counts:
        add_failure(failures, "manifest counts do not match the candidate tree")
    if strict_frozen_baseline and any(actual_counts.get(key) != value for key, value in FROZEN.items()):
        add_failure(failures, "candidate counts do not match the frozen full-corpus baseline")
    if manifest.get("root_sha256") != root_hash(release_root):
        add_failure(failures, "candidate root hash does not match release tree")
    try:
        readme = (release_root / "README.md").read_text(encoding="utf-8")
        notice = (release_root / "NOTICE").read_text(encoding="utf-8")
        citation = (release_root / "CITATION.cff").read_text(encoding="utf-8")
        if manifest.get("release_id") not in readme or manifest.get("release_id", "").removeprefix("v") not in citation:
            add_failure(failures, "public dataset card or citation does not identify the candidate version")
        if "does **not** contain original ORD Parquet payload" not in readme or "distributes no original ORD Parquet payload" not in notice:
            add_failure(failures, "public documentation does not preserve corpus release exclusions")
    except OSError as error:
        add_failure(failures, f"cannot validate release documentation: {error}")

    owner_gates: list[str] = []
    if release_decision_path is None or not release_decision_path.is_file():
        owner_gates = ["F4_explicit_public_HF_dataset_write_authorization"]
    else:
        try:
            decision = read_json(release_decision_path)
            if decision.get("go_no_go") != "go" or not decision.get("public_remote_write_authorized"):
                owner_gates = ["F4_explicit_public_HF_dataset_write_authorization"]
        except (OSError, ValueError):
            owner_gates = ["F4_explicit_public_HF_dataset_write_authorization"]
    status = "rejected" if failures else ("local_validation_passed_pending_publication_authorization" if owner_gates else "accepted_for_authorized_publication")
    return {
        "schema_version": VERSION, "step_id": "step-32-full-corpus-rc-validation", "status": status,
        "blocking_check_failures": len(failures), "blocking_checks": failures, "owner_gates": owner_gates,
        "release_id": manifest.get("release_id"), "payload": {"directories": len(semantic_rows), "files": len(payload_paths), "total_bytes": payload_bytes, "largest_file_bytes": largest_payload},
        "lineage": {"nodes": len(artifact_nodes), "edges": len(edge_rows)}, "root_sha256": root_hash(release_root),
        "remote_write_attempted": False, "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True, type=Path)
    parser.add_argument("--schema-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--release-decision", type=Path)
    parser.add_argument("--no-strict-frozen-baseline", action="store_true")
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(f"refusing to overwrite validation report: {args.report}")
    result = validate(args.release_root, args.schema_dir, args.release_decision, not args.no_strict_frozen_baseline)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
