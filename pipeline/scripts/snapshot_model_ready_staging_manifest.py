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
"""Create a commit-safe model-ready staging manifest without payloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def snapshot(input_path: Path, output_path: Path) -> dict[str, Any]:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite published staging manifest: {output_path}")
    source = json.loads(input_path.read_text(encoding="utf-8"))
    packages = source.get("packages")
    if source.get("schema_version") != "1.0.0" or source.get("step_id") != "step-13" or source.get("status") != "complete" or not isinstance(packages, list) or len(packages) != 19:
        raise ValueError("input is not a complete 19-target step-13 staging manifest")
    records = []
    for package in sorted(packages, key=lambda item: item["target_slug"]):
        artifacts = package["artifacts"]
        required = {"dataset.csv", "schema.json", "yonod-config.json", "row-map.csv", "audit.jsonl", "exclusions.csv", "source-links.json", "target-build-provenance.json", "checksums.csv", "metadata.json"}
        if set(artifacts) != required:
            raise ValueError(f"staged target file set is incomplete: {package['target_slug']}")
        records.append({"target_id": package["target_id"], "target_slug": package["target_slug"], "logical_dataset_id": package["logical_dataset_id"], "readiness_status": package["readiness_status"], "included_count": package["included_count"], "excluded_count": package["excluded_count"], "source_count": package["source_count"], "artifacts": artifacts})
    if sum(record["included_count"] for record in records) != source["included_count"] or sum(record["excluded_count"] for record in records) != source["excluded_count"]:
        raise ValueError("target counts do not sum to staging totals")
    result = {"schema_version": "1.0.0", "step_id": "step-13", "status": "staging_complete_not_released", "staging_run_manifest_sha256": sha256(input_path), "input_hashes": source["input_hashes"], "target_count": 19, "included_count": source["included_count"], "excluded_count": source["excluded_count"], "packages": records}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, output_path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = snapshot(args.input, args.output)
    print(json.dumps({key: result[key] for key in ("target_count", "included_count", "excluded_count")}, sort_keys=True))


if __name__ == "__main__":
    main()
