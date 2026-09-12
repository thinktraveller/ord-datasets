#!/usr/bin/env python3
"""Create compact two-hop lineage indexes for staged corpus and target data."""

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


def write_csv(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(corpus_manifest: Path, target_manifest: Path, output_root: Path) -> dict[str, object]:
    corpus = load(corpus_manifest)["packages"]
    targets = load(target_manifest)["packages"]
    if len(corpus) != 41 or len(targets) != 19:
        raise ValueError("staging manifests do not contain 41 corpus and 19 targets")
    corpus_rows = []
    for package in corpus:
        corpus_rows.append({
            "dataset_slug": package["dataset_slug"],
            "logical_dataset_id": package["logical_dataset_id"],
            "row_count": package["row_count"],
            "reaction_payload_sha256": package.get("reaction_sha256", package["artifacts"]["reactions.csv"]["sha256"]),
            "source_links_path": f"datasets/corpus/{package['dataset_slug']}/source-links.json",
            "row_locator": "physical_dataset_id,source_file,reaction_id,row_index",
            "two_hop_source_manifest": "provenance/source-files.csv",
        })
    target_rows = []
    for package in targets:
        artifacts = package["artifacts"]
        target_rows.append({
            "target_slug": package["target_slug"], "target_id": package["target_id"],
            "logical_dataset_id": package["logical_dataset_id"],
            "included_count": package["included_count"], "excluded_count": package["excluded_count"],
            "row_map_sha256": artifacts["row-map.csv"]["sha256"],
            "audit_sha256": artifacts["audit.jsonl"]["sha256"],
            "exclusions_sha256": artifacts["exclusions.csv"]["sha256"],
            "source_links_path": f"datasets/model-ready/{package['target_slug']}/source-links.json",
            "row_locator": "reaction_key,physical_dataset_id,source_row_index,label_decision_id",
            "two_hop_source_manifest": "provenance/source-files.csv",
        })
    corpus_path = output_root / "corpus-index.csv"
    target_path = output_root / "target-index.csv"
    write_csv(corpus_path, list(corpus_rows[0]), sorted(corpus_rows, key=lambda row: str(row["dataset_slug"])))
    write_csv(target_path, list(target_rows[0]), sorted(target_rows, key=lambda row: str(row["target_slug"])))
    example = output_root / "two-hop-query-examples.md"
    if example.exists():
        raise FileExistsError(f"refusing to overwrite {example}")
    example.write_text(
        "# Two-hop lineage query\n\n"
        "1. For a corpus row, use `physical_dataset_id` and `source_file` in `reactions.csv` to select its dataset "
        "`source-links.json`; for a model-ready row, use the corresponding fields in `row-map.csv` or `exclusions.csv`.\n"
        "2. Match that physical ID in `provenance/source-files.csv` to obtain the fixed upstream URL, Parquet SHA-256, "
        "source reaction count and ORD reaction identifier/row index.\n",
        encoding="utf-8",
    )
    return {
        "schema_version": "1.0.0", "step_id": "step-22", "status": "complete",
        "corpus_index_count": len(corpus_rows), "target_index_count": len(target_rows),
        "corpus_index_sha256": digest(corpus_path), "target_index_sha256": digest(target_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-manifest", type=Path, required=True)
    parser.add_argument("--target-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.corpus_manifest, args.target_manifest, args.output_root)
    if args.report.exists():
        raise FileExistsError(f"refusing to overwrite {args.report}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
