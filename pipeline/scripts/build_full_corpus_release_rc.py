#!/usr/bin/env python3
"""Build an isolated, corpus-only release candidate without remote writes.

The candidate is assembled atomically from the frozen step-11 corpus staging
tree.  It deliberately does not change the staged payload bytes or publish to
Hugging Face.  A later, explicitly authorised transport step may upload only a
candidate that has passed ``validate_full_corpus_release_rc.py``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_corpus_staging import validate as validate_corpus_staging


VERSION = "1.0.0"
RELEASE_DIR = Path("provenance/full-corpus-release")
MANIFEST_RELATIVE = RELEASE_DIR / "release-manifest.json"
PAYLOAD_FILES = ("checksums.csv", "metadata.json", "reactions.csv", "schema.json", "source-links.json")
CATALOG_HEADER = [
    "record_type", "dataset_slug", "display_name_en", "display_name_zh", "logical_dataset_id",
    "physical_dataset_ids_json", "physical_source_files_json", "target_id", "label_type", "label_unit",
    "readiness_status", "artifact_status", "license_id", "row_count", "content_sha256",
    "release_path", "metadata_path", "source_links_path",
]
INVENTORY_HEADER = [
    "artifact_id", "dataset_slug", "logical_dataset_id", "role", "artifact_path", "size_bytes", "sha256",
    "artifact_class", "disposition", "license_id", "redistribution_status", "origin", "source_artifact_ids_json",
]
EDGE_HEADER = ["edge_id", "from_artifact_id", "to_artifact_id", "transformation_id", "relationship", "status"]
FROZEN = {
    "physical_sources_referenced": 53,
    "corpus_packages": 41,
    "corpus_payload_files": 205,
    "corpus_payload_bytes": 13127476889,
    "reactions": 2428291,
}


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


def artifact_id(kind: str, value: str) -> str:
    return f"release-artifact-{kind}-{value.removeprefix('ord_dataset-').replace('_', '-')}"


def root_hash(root: Path) -> str:
    records = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if relative == MANIFEST_RELATIVE:
            continue
        records.append(f"{relative.as_posix()}\t{path.stat().st_size}\t{sha256(path)}")
    return hashlib.sha256(("\n".join(records) + "\n").encode("utf-8")).hexdigest()


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)


def parse_sha256sums(path: Path, *, package_prefix: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            digest, name = line.split(maxsplit=1)
        except ValueError as error:
            raise ValueError(f"malformed SHA256SUMS line {line_number}") from error
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"invalid SHA256SUMS digest at line {line_number}")
        if not name.startswith(package_prefix) or name in entries:
            raise ValueError(f"unexpected or duplicate SHA256SUMS path at line {line_number}: {name}")
        entries[name] = digest
    if not entries:
        raise ValueError("SHA256SUMS has no payload entries")
    return entries


def write_candidate_sha256sums(root: Path, payload_paths: list[Path]) -> dict[str, str]:
    records: dict[str, str] = {}
    for path in sorted(payload_paths, key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        records[f"./{relative}"] = sha256(path)
    (root / "SHA256SUMS").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in records.items()), encoding="utf-8"
    )
    return records


def write_documents(root: Path, dataset_card: Path, release_id: str) -> None:
    shutil.copyfile(dataset_card, root / "README.md")
    (root / "CITATION.cff").write_text(
        "cff-version: 1.2.0\n"
        "message: \"If you use this work, please cite this corpus release and the Open Reaction Database.\"\n"
        "title: \"ORD Processed Reaction Corpus\"\n"
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
        "ORD Processed Reaction Corpus NOTICE\n"
        "=====================================\n\n"
        "The corpus data and data-derived metadata are sanitized derivatives of the Open Reaction Database (ORD), offered under Creative Commons Attribution-ShareAlike 4.0 International. Reuse must retain attribution to ORD, link to the source and license, identify modifications, and comply with ShareAlike.\n\n"
        "This candidate distributes no original ORD Parquet payload, `_needs_review` payload, clean-room duplicate payload, or model-ready target payload. Commit-pinned source URLs, SHA-256 values, and Git LFS identifiers are preserved as provenance metadata.\n\n"
        "The build and validation code is separately licensed under Apache-2.0. No license in this candidate grants rights to material outside its declared scope.\n",
        encoding="utf-8",
    )


def build(
    staging_root: Path,
    semantic_map_path: Path,
    members_path: Path,
    source_files_path: Path,
    control_manifest_path: Path,
    private_transport_sha256sums_path: Path,
    expected_private_transport_sha256: str,
    private_transport_snapshot: str,
    schema_dir: Path,
    project_root: Path,
    dataset_card_path: Path,
    release_root: Path,
    release_id: str,
    project_commit: str,
    build_timestamp: str,
    report_path: Path,
    expected_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    expected = dict(FROZEN if expected_counts is None else expected_counts)
    required_files = [semantic_map_path, members_path, source_files_path, control_manifest_path, private_transport_sha256sums_path, dataset_card_path, project_root / "LICENSE-DATA", project_root / "LICENSE-CODE"]
    for path in required_files:
        require_file(path)
    if not staging_root.is_dir():
        raise NotADirectoryError(staging_root)
    if release_root.exists() or report_path.exists():
        raise FileExistsError("release root or build report already exists; refusing to overwrite an RC")
    if not release_id.startswith("v") or "-corpus-preview" not in release_id:
        raise ValueError("release ID must name the corpus-preview track")
    if len(project_commit) != 40 or any(char not in "0123456789abcdef" for char in project_commit):
        raise ValueError("project commit must be a 40-character lowercase SHA-1")
    if len(expected_private_transport_sha256) != 64:
        raise ValueError("expected private transport SHA256SUMS hash is malformed")
    if sha256(private_transport_sha256sums_path) != expected_private_transport_sha256:
        raise ValueError("private transport SHA256SUMS hash differs from the frozen snapshot")
    private_entries = parse_sha256sums(private_transport_sha256sums_path, package_prefix="./")
    if len(private_entries) != expected["corpus_payload_files"]:
        raise ValueError("private transport SHA256SUMS payload count differs from release scope")

    staging_summary = validate_corpus_staging(
        staging_root, semantic_map_path, members_path, source_files_path, schema_dir, control_manifest_path,
        expected_corpus_count=expected["corpus_packages"],
        expected_physical_count=expected["physical_sources_referenced"],
        expected_reaction_count=expected["reactions"],
    )
    semantic_rows = read_csv(semantic_map_path)
    members_rows = read_csv(members_path)
    source_rows = read_csv(source_files_path)
    semantic_by_slug = {row["directory_slug"]: row for row in semantic_rows}
    source_by_id = {row["physical_dataset_id"]: row for row in source_rows}
    members_by_logical: dict[str, list[dict[str, str]]] = {}
    for row in members_rows:
        members_by_logical.setdefault(row["logical_dataset_id"], []).append(row)
    if len(semantic_by_slug) != expected["corpus_packages"] or len(source_by_id) != expected["physical_sources_referenced"]:
        raise ValueError("frozen source or corpus closure has duplicates")

    metadata_validator = Draft202012Validator(read_json(schema_dir / "dataset-metadata.schema.json"))
    catalog_validator = Draft202012Validator(read_json(schema_dir / "catalog-record.schema.json"))
    artifact_validator = Draft202012Validator(read_json(schema_dir / "artifact-record.schema.json"))
    transformation_validator = Draft202012Validator(read_json(schema_dir / "transformation-record.schema.json"))
    manifest_validator = Draft202012Validator(read_json(schema_dir / "full-corpus-release-manifest.schema.json"))

    release_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = release_root.parent / f".{release_root.name}.{uuid.uuid4().hex}.partial"
    temporary.mkdir()
    try:
        payload_paths: list[Path] = []
        inventory_rows: list[dict[str, Any]] = []
        catalog_csv: list[dict[str, str]] = []
        catalog_json: list[dict[str, Any]] = []
        corpus_nodes: dict[str, str] = {}
        source_nodes: dict[str, str] = {}
        for slug in sorted(semantic_by_slug):
            semantic = semantic_by_slug[slug]
            logical_id = semantic["logical_dataset_id"]
            source_directory = staging_root / slug
            destination = temporary / "datasets" / "corpus" / slug
            destination.mkdir(parents=True)
            for filename in PAYLOAD_FILES:
                source = source_directory / filename
                copied = destination / filename
                shutil.copyfile(source, copied)
                if source.stat().st_size != copied.stat().st_size:
                    raise ValueError(f"payload copy size mismatch: {slug}/{filename}")
                payload_paths.append(copied)
            metadata = read_json(destination / "metadata.json")
            metadata_validator.validate(metadata)
            if metadata["dataset_kind"] != "corpus" or metadata["dataset_slug"] != slug or metadata["logical_dataset_id"] != logical_id:
                raise ValueError(f"copied metadata identity mismatch: {slug}")
            reaction_path = destination / "reactions.csv"
            physical_ids = json.loads(semantic["physical_dataset_ids_json"])
            source_files = json.loads(semantic["physical_source_files_json"])
            catalog_row = {
                "record_type": "corpus", "dataset_slug": slug,
                "display_name_en": semantic["display_name_en"], "display_name_zh": semantic["display_name_zh"],
                "logical_dataset_id": logical_id,
                "physical_dataset_ids_json": json.dumps(physical_ids, ensure_ascii=False),
                "physical_source_files_json": json.dumps(source_files, ensure_ascii=False),
                "target_id": "", "label_type": "", "label_unit": "",
                "readiness_status": metadata["readiness_status"], "artifact_status": metadata["artifact_status"],
                "license_id": "CC-BY-SA-4.0", "row_count": str(metadata["corpus_row_count"]),
                "content_sha256": sha256(reaction_path), "release_path": f"datasets/corpus/{slug}",
                "metadata_path": f"datasets/corpus/{slug}/metadata.json",
                "source_links_path": f"datasets/corpus/{slug}/source-links.json",
            }
            catalog_instance = {
                "schema_version": VERSION, **{key: value for key, value in catalog_row.items() if key not in {"physical_dataset_ids_json", "physical_source_files_json", "row_count", "target_id", "label_type", "label_unit"}},
                "physical_dataset_ids": physical_ids, "physical_source_files": source_files,
                "target_id": None, "label_type": None, "label_unit": None, "row_count": int(catalog_row["row_count"]),
            }
            catalog_validator.validate(catalog_instance)
            catalog_csv.append(catalog_row)
            catalog_json.append(catalog_instance)
            corpus_node = artifact_id("corpus", slug)
            corpus_nodes[logical_id] = corpus_node
            source_ids = []
            for member in sorted(members_by_logical[logical_id], key=lambda item: item["physical_dataset_id"]):
                physical_id = member["physical_dataset_id"]
                source_nodes[physical_id] = artifact_id("source", physical_id)
                source_ids.append(source_nodes[physical_id])
            for path in sorted(destination.iterdir(), key=lambda item: item.name):
                role = path.name.removesuffix(".json").removesuffix(".csv")
                inventory_rows.append({
                    "artifact_id": f"{corpus_node}-{role.replace('_', '-')}", "dataset_slug": slug,
                    "logical_dataset_id": logical_id, "role": role,
                    "artifact_path": path.relative_to(temporary).as_posix(), "size_bytes": path.stat().st_size,
                    "sha256": sha256(path), "artifact_class": "corpus", "disposition": "staged",
                    "license_id": "CC-BY-SA-4.0", "redistribution_status": "pending",
                    "origin": "step-11-corpus-staging", "source_artifact_ids_json": json.dumps(source_ids),
                })

        if len(payload_paths) != expected["corpus_payload_files"] or sum(path.stat().st_size for path in payload_paths) != expected["corpus_payload_bytes"]:
            raise ValueError("candidate payload count or bytes differ from frozen release scope")
        candidate_entries = write_candidate_sha256sums(temporary, payload_paths)
        private_to_candidate = {f"./datasets/corpus/{name.removeprefix('./')}": digest for name, digest in private_entries.items()}
        if candidate_entries != private_to_candidate:
            raise ValueError("candidate payload hashes differ from the verified private transport snapshot")

        write_csv(temporary / "datasets" / "catalog.csv", CATALOG_HEADER, sorted(catalog_csv, key=lambda row: row["dataset_slug"]))
        write_json(temporary / "datasets" / "catalog.json", sorted(catalog_json, key=lambda row: row["dataset_slug"]))
        (temporary / "provenance").mkdir(parents=True)
        shutil.copyfile(source_files_path, temporary / "provenance" / "source-files.initial.csv")
        shutil.copyfile(source_files_path, temporary / "provenance" / "source-files.csv")
        shutil.copyfile(semantic_map_path, temporary / "provenance" / "semantic-name-map.csv")
        shutil.copyfile(members_path, temporary / "provenance" / "logical-dataset-members.csv")
        provenance = temporary / RELEASE_DIR
        provenance.mkdir(parents=True)
        shutil.copyfile(control_manifest_path, provenance / "staging-control-manifest.json")
        shutil.copyfile(private_transport_sha256sums_path, provenance / "private-transport-SHA256SUMS")
        write_csv(provenance / "artifact-inventory.csv", INVENTORY_HEADER, sorted(inventory_rows, key=lambda row: row["artifact_path"]))
        shutil.copyfile(project_root / "LICENSE-DATA", temporary / "LICENSE-DATA")
        shutil.copyfile(project_root / "LICENSE-CODE", temporary / "LICENSE-CODE")
        write_documents(temporary, dataset_card_path, release_id)

        artifact_nodes: list[dict[str, Any]] = []
        for physical_id in sorted(source_nodes):
            source = source_by_id[physical_id]
            artifact_nodes.append({
                "schema_version": VERSION, "artifact_id": source_nodes[physical_id], "artifact_path": source["upstream_path"],
                "object_type": "virtual_object", "size_bytes": int(source["size_bytes"]), "sha256": source["source_sha256"],
                "artifact_class": "source", "disposition": "manifest_only", "license_id": "CC-BY-SA-4.0",
                "redistribution_status": "not_applicable", "origin": source["source_file_url"], "source_artifact_ids": [],
            })
        for slug in sorted(semantic_by_slug):
            semantic = semantic_by_slug[slug]
            logical_id = semantic["logical_dataset_id"]
            source_ids = [source_nodes[item["physical_dataset_id"]] for item in sorted(members_by_logical[logical_id], key=lambda item: item["physical_dataset_id"])]
            reaction = temporary / "datasets" / "corpus" / slug / "reactions.csv"
            artifact_nodes.append({
                "schema_version": VERSION, "artifact_id": corpus_nodes[logical_id], "artifact_path": reaction.relative_to(temporary).as_posix(),
                "object_type": "file", "size_bytes": reaction.stat().st_size, "sha256": sha256(reaction),
                "artifact_class": "corpus", "disposition": "staged", "license_id": "CC-BY-SA-4.0",
                "redistribution_status": "pending", "origin": "step-11-corpus-staging", "source_artifact_ids": source_ids,
            })
        for node in artifact_nodes:
            artifact_validator.validate(node)
        with (provenance / "release-artifacts.jsonl").open("w", encoding="utf-8") as handle:
            for node in sorted(artifact_nodes, key=lambda item: item["artifact_id"]):
                handle.write(json.dumps(node, ensure_ascii=False, sort_keys=True) + "\n")

        edges: list[dict[str, str]] = []
        for index, member in enumerate(sorted(members_rows, key=lambda item: (item["logical_dataset_id"], item["physical_dataset_id"])), 1):
            edges.append({
                "edge_id": f"edge-corpus-source-{index}", "from_artifact_id": source_nodes[member["physical_dataset_id"]],
                "to_artifact_id": corpus_nodes[member["logical_dataset_id"]], "transformation_id": "transform-full-corpus-rc",
                "relationship": "derived_from", "status": "complete",
            })
        write_csv(provenance / "lineage-edges.csv", EDGE_HEADER, edges)
        transformation = {
            "schema_version": VERSION, "transformation_id": "transform-full-corpus-rc", "step_id": "step-31",
            "tool": "build_full_corpus_release_rc.py", "pipeline_commit": project_commit,
            "command": "python pipeline/scripts/build_full_corpus_release_rc.py --staging-root <staging-root> --release-root <release-root>",
            "config_sha256": sha256(control_manifest_path), "input_artifact_ids": sorted(source_nodes.values()),
            "output_artifact_ids": sorted(corpus_nodes.values()), "started_at": build_timestamp, "ended_at": build_timestamp,
            "status": "complete", "error_code": None,
        }
        transformation_validator.validate(transformation)
        (provenance / "transformations.jsonl").write_text(json.dumps(transformation, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

        counts = {
            "physical_sources_referenced": len(source_nodes), "corpus_packages": len(corpus_nodes),
            "corpus_payload_files": len(payload_paths), "corpus_payload_bytes": sum(path.stat().st_size for path in payload_paths),
            "reactions": staging_summary["reaction_count"], "largest_corpus_file_bytes": max(path.stat().st_size for path in payload_paths),
        }
        if any(counts[key] != expected[key] for key in ("physical_sources_referenced", "corpus_packages", "corpus_payload_files", "corpus_payload_bytes", "reactions")):
            raise ValueError("candidate counts differ from frozen release scope")
        manifest = {
            "schema_version": VERSION, "release_id": release_id, "release_status": "local-release-candidate",
            "release_track": "corpus-public-release", "project_commit": project_commit,
            "ord_upstream_revision": source_rows[0]["upstream_revision"],
            "source_manifest_path": "provenance/source-files.initial.csv", "source_manifest_sha256": sha256(temporary / "provenance" / "source-files.initial.csv"),
            "semantic_map_path": "provenance/semantic-name-map.csv", "semantic_map_sha256": sha256(temporary / "provenance" / "semantic-name-map.csv"),
            "members_path": "provenance/logical-dataset-members.csv", "members_sha256": sha256(temporary / "provenance" / "logical-dataset-members.csv"),
            "staging_control_manifest_path": "provenance/full-corpus-release/staging-control-manifest.json", "staging_control_manifest_sha256": sha256(provenance / "staging-control-manifest.json"),
            "private_transport_snapshot": private_transport_snapshot,
            "contract_versions": {"catalog": VERSION, "metadata": VERSION, "source_links": VERSION, "artifact_inventory": VERSION, "transformation": VERSION, "release_manifest": VERSION, "csv_contracts": "1.1.0"},
            "counts": counts,
            "excluded_payloads": ["original ORD Parquet payload", "_needs_review payload", "clean-room duplicate payload", "model-ready target payload"],
            "license": {"data_license_id": "CC-BY-SA-4.0", "code_license_id": "Apache-2.0", "notice_path": "NOTICE"},
            "catalog_path": "datasets/catalog.csv", "artifact_inventory_path": "provenance/full-corpus-release/artifact-inventory.csv",
            "release_artifacts_path": "provenance/full-corpus-release/release-artifacts.jsonl", "transformations_path": "provenance/full-corpus-release/transformations.jsonl",
            "lineage_edges_path": "provenance/full-corpus-release/lineage-edges.csv", "sha256sums_path": "SHA256SUMS", "sha256sums_sha256": sha256(temporary / "SHA256SUMS"),
            "private_transport_sha256sums_path": "provenance/full-corpus-release/private-transport-SHA256SUMS", "private_transport_sha256sums_sha256": sha256(provenance / "private-transport-SHA256SUMS"),
            "root_hash_scope": "all candidate tree files excluding provenance/full-corpus-release/release-manifest.json", "root_sha256": root_hash(temporary),
            "publication": {"repository": "thinktraveller/ord-processed-reaction-corpus", "repo_type": "dataset", "visibility": "public", "remote_write_attempted": False},
        }
        manifest_validator.validate(manifest)
        write_json(temporary / MANIFEST_RELATIVE, manifest)
        if root_hash(temporary) != manifest["root_sha256"]:
            raise ValueError("candidate root hash changed while writing the manifest")
        result = {
            "schema_version": VERSION, "step_id": "step-31-full-corpus-rc-build", "status": "complete",
            "release_id": release_id, "release_root": release_root.as_posix(), "counts": counts,
            "private_transport_snapshot": private_transport_snapshot, "private_transport_sha256sums_sha256": expected_private_transport_sha256,
            "root_sha256": manifest["root_sha256"], "remote_write_attempted": False,
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(report_path, result)
        temporary.replace(release_root)
        return result
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-root", required=True, type=Path)
    parser.add_argument("--semantic-map", required=True, type=Path)
    parser.add_argument("--members", required=True, type=Path)
    parser.add_argument("--source-files", required=True, type=Path)
    parser.add_argument("--control-manifest", required=True, type=Path)
    parser.add_argument("--private-transport-sha256sums", required=True, type=Path)
    parser.add_argument("--expected-private-transport-sha256", required=True)
    parser.add_argument("--private-transport-snapshot", required=True)
    parser.add_argument("--schema-dir", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--dataset-card", required=True, type=Path)
    parser.add_argument("--release-root", required=True, type=Path)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--project-commit", required=True)
    parser.add_argument("--build-timestamp", required=True)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(**vars(args)), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
