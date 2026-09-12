#!/usr/bin/env python3
"""Validate an isolated model-ready preview RC without any remote writes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

VERSION = "1.0.0"
PREVIEW_DIR = Path("provenance/model-ready-preview")
MANIFEST_RELATIVE = PREVIEW_DIR / "release-manifest.json"
PAYLOAD_FILES = {
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
}
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
FROZEN_COUNTS = {
    "physical_sources_referenced": 18,
    "logical_corpus_references": 15,
    "model_ready_packages": 15,
    "model_ready_targets": 19,
    "target_payload_files": 190,
    "target_payload_bytes": 211008093,
    "largest_target_file_bytes": 54055777,
}
FROZEN_STATUSES = {
    "active_generated_pending_release_validation": 7,
    "generated_adapter_blocked": 1,
    "generated_pending_campaign_evaluation": 6,
    "generated_with_source_caveat": 1,
    "partial_scope_generated": 1,
    "research_only_benchmark_blocked": 3,
}
EMAIL = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CREDENTIAL_PATTERNS = [
    re.compile(rb"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----"),
    re.compile(rb"(?:ghp|github_pat)_[A-Za-z0-9_]{20,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
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


def root_hash(root: Path) -> str:
    records = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if relative == MANIFEST_RELATIVE:
            continue
        records.append(f"{relative.as_posix()}\t{path.stat().st_size}\t{sha256(path)}")
    return hashlib.sha256(("\n".join(records) + "\n").encode("utf-8")).hexdigest()


def add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def scan_release_tree(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        tail = b""
        categories: set[str] = set()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                chunk = tail + block
                if EMAIL.search(chunk):
                    categories.add("email")
                if any(pattern.search(chunk) for pattern in CREDENTIAL_PATTERNS):
                    categories.add("credential")
                tail = chunk[-256:]
        findings.extend({"path": relative, "category": category, "severity": "blocking"} for category in sorted(categories))
    return findings


def validate(
    release_root: Path,
    schema_dir: Path,
    strict_frozen_baseline: bool = True,
    release_decision_path: Path | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[dict[str, Any]] = []
    if not release_root.is_dir():
        return {
            "schema_version": VERSION,
            "step_id": "step-27-preview",
            "status": "rejected",
            "blocking_check_failures": 1,
            "blocking_checks": ["release root is not a directory"],
            "remote_write_attempted": False,
        }
    for required in (
        MANIFEST_RELATIVE,
        Path("datasets/catalog.csv"),
        Path("datasets/catalog.json"),
        Path("provenance/source-files.initial.csv"),
        Path("provenance/semantic-target-map.csv"),
        PREVIEW_DIR / "artifact-inventory.csv",
        PREVIEW_DIR / "release-artifacts.jsonl",
        PREVIEW_DIR / "lineage-edges.csv",
        PREVIEW_DIR / "transformations.jsonl",
        Path("README.md"),
        Path("DATA_CARD.md"),
        Path("CITATION.cff"),
        Path("NOTICE"),
        Path("LICENSE-DATA"),
        Path("LICENSE-CODE"),
    ):
        if not (release_root / required).is_file():
            add_failure(failures, f"missing required release file: {required.as_posix()}")
    if failures:
        return {
            "schema_version": VERSION,
            "step_id": "step-27-preview",
            "status": "rejected",
            "blocking_check_failures": len(failures),
            "blocking_checks": failures,
            "remote_write_attempted": False,
        }

    try:
        manifest = read_json(release_root / MANIFEST_RELATIVE)
        Draft202012Validator(read_json(schema_dir / "model-ready-preview-release-manifest.schema.json")).validate(manifest)
    except (OSError, ValueError, ValidationError) as error:
        add_failure(failures, f"invalid preview manifest: {error.message if isinstance(error, ValidationError) else error}")
        manifest = {}
    try:
        metadata_validator = Draft202012Validator(read_json(schema_dir / "dataset-metadata.schema.json"))
        links_validator = Draft202012Validator(read_json(schema_dir / "source-links.schema.json"))
        catalog_validator = Draft202012Validator(read_json(schema_dir / "catalog-record.schema.json"))
        artifact_validator = Draft202012Validator(read_json(schema_dir / "artifact-record.schema.json"))
        transformation_validator = Draft202012Validator(read_json(schema_dir / "transformation-record.schema.json"))
    except (OSError, ValueError, ValidationError) as error:
        add_failure(failures, f"invalid validation schema: {error}")
        metadata_validator = links_validator = catalog_validator = artifact_validator = transformation_validator = None

    banned = [
        path.relative_to(release_root).as_posix()
        for path in release_root.rglob("*")
        if path.is_file()
        and (
            path.suffix == ".parquet"
            or "_needs_review" in path.relative_to(release_root).parts
            or path.relative_to(release_root).as_posix().startswith("datasets/corpus/")
        )
    ]
    if banned:
        add_failure(failures, f"excluded payload present: {', '.join(sorted(banned))}")
    corpus_path = release_root / "datasets/corpus"
    if corpus_path.exists():
        add_failure(failures, "datasets/corpus exists in model-ready-only preview")

    payload_paths = sorted(path for path in (release_root / "datasets/model-ready").rglob("*") if path.is_file()) if (release_root / "datasets/model-ready").is_dir() else []
    target_dirs = sorted(path for path in (release_root / "datasets/model-ready").iterdir() if path.is_dir()) if (release_root / "datasets/model-ready").is_dir() else []
    if len(target_dirs) != 19:
        add_failure(failures, f"expected 19 target directories, found {len(target_dirs)}")
    if len(payload_paths) != 190:
        add_failure(failures, f"expected 190 target payload files, found {len(payload_paths)}")
    payload_bytes = sum(path.stat().st_size for path in payload_paths)
    largest_path = max(payload_paths, key=lambda path: path.stat().st_size, default=None)
    largest_bytes = largest_path.stat().st_size if largest_path else 0

    catalog_rows = []
    try:
        with (release_root / "datasets/catalog.csv").open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != CATALOG_HEADER:
                add_failure(failures, "preview catalog CSV header differs from contract")
            catalog_rows = list(reader)
        catalog_json = read_json(release_root / "datasets/catalog.json")
        if not isinstance(catalog_json, list):
            add_failure(failures, "preview catalog JSON is not an array")
            catalog_json = []
    except (OSError, ValueError, csv.Error) as error:
        add_failure(failures, f"cannot read preview catalog: {error}")
        catalog_json = []
    if len(catalog_rows) != 19 or len({row.get("dataset_slug") for row in catalog_rows}) != 19:
        add_failure(failures, "preview catalog does not contain exactly 19 unique targets")
    catalog_by_slug: dict[str, dict[str, str]] = {}
    for row in catalog_rows:
        try:
            instance = {
                "schema_version": VERSION,
                **{key: value for key, value in row.items() if key not in {"physical_dataset_ids_json", "physical_source_files_json", "row_count"}},
                "physical_dataset_ids": json.loads(row["physical_dataset_ids_json"]),
                "physical_source_files": json.loads(row["physical_source_files_json"]),
                "row_count": int(row["row_count"]),
            }
            if catalog_validator is not None:
                catalog_validator.validate(instance)
            catalog_by_slug[row["dataset_slug"]] = row
        except (KeyError, ValueError, TypeError, ValidationError) as error:
            add_failure(failures, f"invalid catalog record: {error}")
    if catalog_json != [
        {
            "schema_version": VERSION,
            **{key: value for key, value in row.items() if key not in {"physical_dataset_ids_json", "physical_source_files_json", "row_count"}},
            "physical_dataset_ids": json.loads(row["physical_dataset_ids_json"]),
            "physical_source_files": json.loads(row["physical_source_files_json"]),
            "row_count": int(row["row_count"]),
        }
        for row in sorted(catalog_rows, key=lambda row: row["dataset_slug"])
    ]:
        add_failure(failures, "preview catalog JSON and CSV are not semantically identical")

    try:
        with (release_root / "provenance/source-files.initial.csv").open(encoding="utf-8", newline="") as handle:
            source_by_id = {row["physical_dataset_id"]: row for row in csv.DictReader(handle)}
        if len(source_by_id) != 53:
            add_failure(failures, "preview source manifest does not preserve 53 frozen sources")
        if manifest.get("source_manifest_sha256") != sha256(release_root / "provenance/source-files.initial.csv"):
            add_failure(failures, "preview source manifest hash differs from manifest")
    except (OSError, KeyError, csv.Error) as error:
        add_failure(failures, f"cannot read frozen source manifest: {error}")
        source_by_id = {}

    target_statuses: Counter[str] = Counter()
    actual_inventory_paths: set[str] = set()
    for directory in target_dirs:
        slug = directory.name
        files = {path.name for path in directory.iterdir() if path.is_file()}
        if files != PAYLOAD_FILES:
            add_failure(failures, f"unexpected target file set: {slug}")
            continue
        row = catalog_by_slug.get(slug)
        if row is None:
            add_failure(failures, f"target directory missing from catalog: {slug}")
            continue
        try:
            metadata = read_json(directory / "metadata.json")
            source_links = read_json(directory / "source-links.json")
            if metadata_validator is not None:
                metadata_validator.validate(metadata)
            if links_validator is not None:
                links_validator.validate(source_links)
            if (
                metadata["dataset_kind"] != "model-ready"
                or metadata["dataset_slug"] != slug
                or metadata["target_id"] != row["target_id"]
                or metadata["logical_dataset_id"] != row["logical_dataset_id"]
                or metadata["readiness_status"] != row["readiness_status"]
                or metadata["artifact_status"] != "staged"
                or metadata["label"]["type"] != row["label_type"]
                or metadata["label"]["unit"] != row["label_unit"]
            ):
                add_failure(failures, f"metadata/catalog semantic mismatch: {slug}")
            if row["content_sha256"] != sha256(directory / "dataset.csv"):
                add_failure(failures, f"catalog dataset hash mismatch: {slug}")
            if row["release_path"] != f"datasets/model-ready/{slug}" or row["metadata_path"] != f"datasets/model-ready/{slug}/metadata.json" or row["source_links_path"] != f"datasets/model-ready/{slug}/source-links.json":
                add_failure(failures, f"catalog release paths are not target-local: {slug}")
            physical_ids = json.loads(row["physical_dataset_ids_json"])
            source_files = json.loads(row["physical_source_files_json"])
            linked = [(item["physical_dataset_id"], item["source_file"]) for item in source_links["links"]]
            if linked != list(zip(physical_ids, source_files, strict=True)):
                add_failure(failures, f"target source-link closure differs from catalog: {slug}")
            for link in source_links["links"]:
                frozen = source_by_id.get(link["physical_dataset_id"])
                if frozen is None:
                    add_failure(failures, f"target links an unknown frozen source: {slug}")
                    continue
                for link_field, source_field in (
                    ("source_file", "upstream_path"),
                    ("upstream_revision", "upstream_revision"),
                    ("source_file_url", "source_file_url"),
                    ("source_sha256", "source_sha256"),
                    ("git_lfs_oid", "git_lfs_oid"),
                    ("data_license_id", "data_license_id"),
                ):
                    if link[link_field] != frozen[source_field]:
                        add_failure(failures, f"target source link is not frozen: {slug}/{link_field}")
            checksums = {item["role"]: item for item in read_csv(directory / "checksums.csv")}
            if set(checksums) != set(CHECKSUM_FILES):
                add_failure(failures, f"target checksum roles differ from contract: {slug}")
            for role, filename in CHECKSUM_FILES.items():
                item = checksums.get(role)
                path = directory / filename
                if item is None or item.get("path") != filename or item.get("sha256") != sha256(path) or item.get("size_bytes") != str(path.stat().st_size):
                    add_failure(failures, f"target checksum mismatch: {slug}/{filename}")
            target_statuses[row["readiness_status"]] += 1
            actual_inventory_paths.update(path.relative_to(release_root).as_posix() for path in directory.iterdir() if path.is_file())
        except (OSError, KeyError, TypeError, ValueError, ValidationError, csv.Error) as error:
            add_failure(failures, f"invalid target package {slug}: {error}")

    inventory_rows = []
    try:
        with (release_root / PREVIEW_DIR / "artifact-inventory.csv").open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != INVENTORY_HEADER:
                add_failure(failures, "preview artifact inventory header differs from contract")
            inventory_rows = list(reader)
        inventory_paths = {row["artifact_path"] for row in inventory_rows}
        if len(inventory_rows) != 190 or len(inventory_paths) != 190:
            add_failure(failures, "preview artifact inventory does not contain exactly 190 unique payload files")
        if inventory_paths != actual_inventory_paths:
            add_failure(failures, "preview artifact inventory is not the exact target payload closure")
        for row in inventory_rows:
            path = release_root / row["artifact_path"]
            if not path.is_file() or row["sha256"] != sha256(path) or row["size_bytes"] != str(path.stat().st_size):
                add_failure(failures, f"preview artifact inventory hash mismatch: {row['artifact_path']}")
    except (OSError, KeyError, csv.Error) as error:
        add_failure(failures, f"cannot validate preview artifact inventory: {error}")

    artifact_nodes = []
    try:
        with (release_root / PREVIEW_DIR / "release-artifacts.jsonl").open(encoding="utf-8") as handle:
            artifact_nodes = [json.loads(line) for line in handle if line.strip()]
        for node in artifact_nodes:
            if artifact_validator is not None:
                artifact_validator.validate(node)
        node_ids = {node["artifact_id"] for node in artifact_nodes}
        if len(node_ids) != len(artifact_nodes):
            add_failure(failures, "preview lineage nodes contain duplicate artifact IDs")
        source_nodes = [node for node in artifact_nodes if node["artifact_class"] == "source"]
        reference_nodes = [node for node in artifact_nodes if node["artifact_class"] == "corpus"]
        target_nodes = [node for node in artifact_nodes if node["artifact_class"] == "model-ready"]
        if len(reference_nodes) != 15 or any(node["disposition"] != "manifest_only" or node["sha256"] is not None for node in reference_nodes):
            add_failure(failures, "corpus lineage nodes are not exactly 15 reference-only virtual nodes")
        if len(target_nodes) != 19 or {node["artifact_path"] for node in target_nodes} != {f"datasets/model-ready/{slug}/dataset.csv" for slug in catalog_by_slug}:
            add_failure(failures, "target lineage nodes do not match the 19 preview datasets")
    except (OSError, KeyError, TypeError, ValueError, ValidationError) as error:
        add_failure(failures, f"cannot validate preview lineage nodes: {error}")
        source_nodes = reference_nodes = target_nodes = []
        node_ids = set()

    try:
        edge_rows = read_csv(release_root / PREVIEW_DIR / "lineage-edges.csv")
        if not edge_rows or any(row["status"] != "complete" for row in edge_rows):
            add_failure(failures, "preview lineage has missing or non-complete edges")
        if any(row["from_artifact_id"] not in node_ids or row["to_artifact_id"] not in node_ids for row in edge_rows):
            add_failure(failures, "preview lineage edge references an unknown node")
        incoming_targets = {row["to_artifact_id"] for row in edge_rows if row["relationship"] == "projects"}
        if incoming_targets != {node["artifact_id"] for node in target_nodes}:
            add_failure(failures, "each target must have exactly a reference-only corpus projection edge")
    except (OSError, KeyError, csv.Error) as error:
        add_failure(failures, f"cannot validate preview lineage edges: {error}")
        edge_rows = []
    try:
        transformations = [json.loads(line) for line in (release_root / PREVIEW_DIR / "transformations.jsonl").read_text(encoding="utf-8").splitlines() if line]
        if len(transformations) != 1:
            add_failure(failures, "preview must contain exactly one RC transformation record")
        for record in transformations:
            if transformation_validator is not None:
                transformation_validator.validate(record)
    except (OSError, ValueError, ValidationError) as error:
        add_failure(failures, f"cannot validate preview transformation record: {error}")

    actual_root = root_hash(release_root)
    if manifest.get("root_sha256") != actual_root:
        add_failure(failures, "preview root hash does not match release tree")
    if manifest.get("counts"):
        actual_counts = {
            "physical_sources_referenced": len(source_nodes),
            "logical_corpus_references": len(reference_nodes),
            "model_ready_packages": len(reference_nodes),
            "model_ready_targets": len(target_dirs),
            "target_payload_files": len(payload_paths),
            "target_payload_bytes": payload_bytes,
            "largest_target_file_bytes": largest_bytes,
        }
        if manifest["counts"] != actual_counts:
            add_failure(failures, "preview manifest counts do not match release tree")
        if strict_frozen_baseline and actual_counts != FROZEN_COUNTS:
            add_failure(failures, "preview counts do not match the frozen 19-target baseline")
    if strict_frozen_baseline and dict(sorted(target_statuses.items())) != FROZEN_STATUSES:
        add_failure(failures, "preview target readiness-status distribution differs from frozen baseline")
    if largest_path is not None and largest_bytes > 50 * 1024 * 1024:
        warnings.append(
            {
                "check": "ordinary_git_large_file_warning",
                "path": largest_path.relative_to(release_root).as_posix(),
                "size_bytes": largest_bytes,
                "owner": "project-owner",
                "reason": "The selected transport must document the >50 MiB warning and perform required readback before release.",
            }
        )
    try:
        readme = (release_root / "README.md").read_text(encoding="utf-8").lower()
        data_card = (release_root / "DATA_CARD.md").read_text(encoding="utf-8").lower()
        if "not a complete ord corpus release" not in readme or "not an accepted benchmark" not in readme or "not be presented as accepted benchmarks" not in data_card:
            add_failure(failures, "preview documentation does not preserve scope and readiness disclaimers")
    except OSError as error:
        add_failure(failures, f"cannot validate preview documentation: {error}")
    findings = scan_release_tree(release_root)
    if findings:
        add_failure(failures, "release-tree sensitive scan found blocking credential or email evidence")

    owner_gates = []
    if release_decision_path is None or not release_decision_path.is_file():
        owner_gates = ["B3_transport_pilot_authorization_and_readback", "B4_release_decision_and_remote_write_authorization"]
    else:
        try:
            decision = read_json(release_decision_path)
            if decision.get("go_no_go") != "go" or not decision.get("remote_write_authorized"):
                owner_gates = ["B3_transport_pilot_authorization_and_readback", "B4_release_decision_and_remote_write_authorization"]
        except (OSError, ValueError):
            owner_gates = ["B3_transport_pilot_authorization_and_readback", "B4_release_decision_and_remote_write_authorization"]
    status = "rejected" if failures else ("local_validation_passed_pending_owner_gates" if owner_gates else "accepted_for_authorized_upload")
    return {
        "schema_version": VERSION,
        "step_id": "step-27-preview",
        "status": status,
        "blocking_check_failures": len(failures),
        "blocking_checks": failures,
        "owner_gates": owner_gates,
        "release_id": manifest.get("release_id"),
        "payload": {"target_directories": len(target_dirs), "files": len(payload_paths), "total_bytes": payload_bytes, "largest_file_bytes": largest_bytes},
        "lineage": {"nodes": len(artifact_nodes), "source_nodes": len(source_nodes), "reference_only_corpus_nodes": len(reference_nodes), "target_nodes": len(target_nodes), "edges": len(edge_rows)},
        "readiness_status_counts": dict(sorted(target_statuses.items())),
        "root_sha256": actual_root,
        "warnings": warnings,
        "sensitive_scan": {"blocking_findings": len(findings), "findings": findings},
        "remote_write_attempted": False,
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
        raise FileExistsError(f"refusing to overwrite preview validation report: {args.report}")
    result = validate(
        args.release_root,
        args.schema_dir,
        strict_frozen_baseline=not args.no_strict_frozen_baseline,
        release_decision_path=args.release_decision,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
