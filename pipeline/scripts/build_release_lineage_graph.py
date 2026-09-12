#!/usr/bin/env python3
"""Assemble the compact, content-addressed lineage graph for a local draft."""

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


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def artifact_id(kind: str, value: str) -> str:
    return f"release-artifact-{kind}-{value.replace('_', '-')}"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["edge_id", "from_artifact_id", "to_artifact_id", "transformation_id", "relationship", "status"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(source_path: Path, members_path: Path, corpus_manifest: Path, target_manifest: Path, output_root: Path, project_commit: str) -> dict[str, Any]:
    sources = read_csv(source_path)
    members = read_csv(members_path)
    corpus = load(corpus_manifest)["packages"]
    targets = load(target_manifest)["packages"]
    if len(sources) != 53 or len(members) != 53 or len(corpus) != 41 or len(targets) != 19:
        raise ValueError("lineage inputs do not meet the frozen 53/53/41/19 baseline")
    corpus_by_logical = {row["logical_dataset_id"]: row for row in corpus}
    source_by_id = {row["physical_dataset_id"]: row for row in sources}
    nodes: list[dict[str, Any]] = []
    for source in sources:
        identifier = artifact_id("source", source["physical_dataset_id"].split("-")[-1])
        nodes.append({"schema_version": "1.0.0", "artifact_id": identifier, "artifact_path": source["upstream_path"], "object_type": "virtual_object", "size_bytes": int(source["size_bytes"]), "sha256": source["source_sha256"], "artifact_class": "source", "disposition": "staged", "license_id": "CC-BY-SA-4.0", "redistribution_status": "not_applicable", "origin": source["source_file_url"], "source_artifact_ids": []})
    for package in corpus:
        nodes.append({"schema_version": "1.0.0", "artifact_id": artifact_id("corpus", package["dataset_slug"]), "artifact_path": f"datasets/corpus/{package['dataset_slug']}/reactions.csv", "object_type": "virtual_object", "size_bytes": int(package["artifacts"]["reactions.csv"]["size_bytes"]), "sha256": package["artifacts"]["reactions.csv"]["sha256"], "artifact_class": "corpus", "disposition": "staged", "license_id": "CC-BY-SA-4.0", "redistribution_status": "pending", "origin": "step-11-sanitized-corpus-staging", "source_artifact_ids": []})
    for package in targets:
        nodes.append({"schema_version": "1.0.0", "artifact_id": artifact_id("target", package["target_slug"]), "artifact_path": f"datasets/model-ready/{package['target_slug']}/dataset.csv", "object_type": "virtual_object", "size_bytes": int(package["artifacts"]["dataset.csv"]["size_bytes"]), "sha256": package["artifacts"]["dataset.csv"]["sha256"], "artifact_class": "model-ready", "disposition": "staged", "license_id": "CC-BY-SA-4.0", "redistribution_status": "pending", "origin": "step-13-model-ready-staging", "source_artifact_ids": []})
    edge_rows = []
    for index, member in enumerate(sorted(members, key=lambda row: (row["logical_dataset_id"], row["physical_dataset_id"])), 1):
        source = source_by_id[member["physical_dataset_id"]]
        corpus_package = corpus_by_logical[member["logical_dataset_id"]]
        edge_rows.append({"edge_id": f"edge-source-corpus-{index}", "from_artifact_id": artifact_id("source", source["physical_dataset_id"].split("-")[-1]), "to_artifact_id": artifact_id("corpus", corpus_package["dataset_slug"]), "transformation_id": "transform-step-11-corpus-staging", "relationship": "derived_from", "status": "complete"})
    for index, target in enumerate(sorted(targets, key=lambda row: row["target_slug"]), 1):
        corpus_package = corpus_by_logical[target["logical_dataset_id"]]
        edge_rows.append({"edge_id": f"edge-corpus-target-{index}", "from_artifact_id": artifact_id("corpus", corpus_package["dataset_slug"]), "to_artifact_id": artifact_id("target", target["target_slug"]), "transformation_id": "transform-step-13-model-ready-staging", "relationship": "projects", "status": "complete"})
    node_path = output_root / "release-artifacts.jsonl"
    edge_path = output_root / "lineage-edges.csv"
    transformations_path = output_root / "transformations.jsonl"
    if any(path.exists() for path in (node_path, edge_path, transformations_path)):
        raise FileExistsError("refusing to overwrite release lineage files")
    with node_path.open("w", encoding="utf-8") as handle:
        for node in nodes:
            handle.write(json.dumps(node, ensure_ascii=False, sort_keys=True) + "\n")
    write_csv(edge_path, edge_rows)
    transformations = [
        {"schema_version": "1.0.0", "transformation_id": "transform-step-11-corpus-staging", "step_id": "step-11", "tool": "build_corpus_staging.py", "pipeline_commit": project_commit, "command": "python pipeline/scripts/build_corpus_staging.py --source-root <source-root> --output-root <staging-root>", "config_sha256": digest(corpus_manifest), "input_artifact_ids": [artifact_id("source", source["physical_dataset_id"].split("-")[-1]) for source in sources], "output_artifact_ids": [artifact_id("corpus", item["dataset_slug"]) for item in corpus], "started_at": "2026-09-12T00:00:00+00:00", "ended_at": "2026-09-12T00:00:00+00:00", "status": "complete", "error_code": None},
        {"schema_version": "1.0.0", "transformation_id": "transform-step-13-model-ready-staging", "step_id": "step-13", "tool": "build_model_ready_staging.py", "pipeline_commit": project_commit, "command": "python pipeline/scripts/build_model_ready_staging.py --processing-root <processing-root> --output-root <staging-root>", "config_sha256": digest(target_manifest), "input_artifact_ids": [artifact_id("corpus", item["dataset_slug"]) for item in corpus], "output_artifact_ids": [artifact_id("target", item["target_slug"]) for item in targets], "started_at": "2026-09-12T00:00:00+00:00", "ended_at": "2026-09-12T00:00:00+00:00", "status": "complete", "error_code": None},
    ]
    with transformations_path.open("w", encoding="utf-8") as handle:
        for transformation in transformations:
            handle.write(json.dumps(transformation, ensure_ascii=False, sort_keys=True) + "\n")
    root = hashlib.sha256("\n".join(sorted(f"{node['artifact_id']}:{node['sha256']}" for node in nodes)).encode()).hexdigest()
    return {"schema_version": "1.0.0", "step_id": "step-23", "status": "draft_complete", "node_count": len(nodes), "edge_count": len(edge_rows), "root_sha256": root, "release_artifacts_sha256": digest(node_path), "lineage_edges_sha256": digest(edge_path), "transformations_sha256": digest(transformations_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-files", type=Path, required=True)
    parser.add_argument("--members", type=Path, required=True)
    parser.add_argument("--corpus-manifest", type=Path, required=True)
    parser.add_argument("--target-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--project-commit", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source_files, args.members, args.corpus_manifest, args.target_manifest, args.output_root, args.project_commit)
    if args.report.exists():
        raise FileExistsError(f"refusing to overwrite {args.report}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
