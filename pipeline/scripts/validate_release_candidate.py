#!/usr/bin/env python3
"""Run local release-candidate control-plane checks without remote writes."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(root: Path) -> dict:
    catalog = list(csv.DictReader((root / "datasets/catalog.csv").open(encoding="utf-8", newline="")))
    corpus = [row for row in catalog if row["record_type"] == "corpus"]
    targets = [row for row in catalog if row["record_type"] == "model-ready"]
    graph_nodes = sum(1 for _ in (root / "provenance/release-artifacts.jsonl").open(encoding="utf-8"))
    graph_edges = list(csv.DictReader((root / "provenance/lineage-edges.csv").open(encoding="utf-8", newline="")))
    staged_corpus = [path for path in (root / ".staging/ord-datasets-v0/step-11/datasets/corpus").iterdir() if path.is_dir()]
    staged_targets = [path for path in (root / ".staging/ord-datasets-v0/step-13/datasets/model-ready").iterdir() if path.is_dir()]
    blockers = []
    for name, path in {
        "dependency_lock": root / "pipeline/uv.lock",
        "clean_room_rebuild": root / "reports/release-acceptance/step-20-clean-room-rebuild.json",
        "storage_pilot": root / "reports/release-acceptance/step-25-storage-pilot.json",
        "release_authorization": root / "provenance/release-decision.json",
    }.items():
        if name == "dependency_lock":
            if not path.is_file():
                blockers.append(name)
        elif not path.is_file() or load(path).get("status") not in {"complete", "go"}:
            blockers.append(name)
    return {
        "schema_version": "1.0.0", "step_id": "step-27",
        "status": "complete" if not blockers else "rejected",
        "blocking_check_failures": len(blockers), "blocking_checks": blockers,
        "catalog": {"corpus": len(corpus), "model_ready_targets": len(targets)},
        "staging": {"corpus": len(staged_corpus), "model_ready_targets": len(staged_targets)},
        "lineage": {"nodes": graph_nodes, "edges": len(graph_edges), "failed_edges": sum(edge["status"] != "complete" for edge in graph_edges)},
        "remote_write_attempted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.root)
    if args.report.exists():
        raise FileExistsError(f"refusing to overwrite {args.report}")
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
