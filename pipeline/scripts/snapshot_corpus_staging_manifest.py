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
"""Create a small, commit-safe control-plane manifest for corpus staging."""

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


def snapshot(staging_manifest_path: Path, audit_root: Path, output_path: Path) -> dict[str, Any]:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite published staging manifest: {output_path}")
    staging = json.loads(staging_manifest_path.read_text(encoding="utf-8"))
    if staging.get("schema_version") != "1.0.0" or staging.get("step_id") != "step-11" or staging.get("status") != "complete":
        raise ValueError("input is not a complete step-11 staging manifest")
    packages = staging.get("packages")
    if not isinstance(packages, list) or len(packages) != staging.get("corpus_count"):
        raise ValueError("staging package count is inconsistent")
    records = []
    for package in sorted(packages, key=lambda item: item["dataset_slug"]):
        if package["remaining_literal_email_values"] != 0:
            raise ValueError("cannot publish a staging summary with remaining literal email values")
        if package["redaction"]["output_sha256"] != package["artifacts"]["reactions.csv"]["sha256"]:
            raise ValueError("redaction output hash disagrees with staged reactions hash")
        audit_name = Path(package["redaction_audit"]).name
        audit_path = audit_root / audit_name
        if not audit_path.is_file():
            raise FileNotFoundError(f"missing redaction audit for {package['dataset_slug']}")
        records.append(
            {
                "dataset_slug": package["dataset_slug"],
                "logical_dataset_id": package["logical_dataset_id"],
                "row_count": package["row_count"],
                "reaction_sha256": package["artifacts"]["reactions.csv"]["sha256"],
                "reaction_size_bytes": package["artifacts"]["reactions.csv"]["size_bytes"],
                "metadata_sha256": package["artifacts"]["metadata.json"]["sha256"],
                "source_links_sha256": package["artifacts"]["source-links.json"]["sha256"],
                "checksums_sha256": package["artifacts"]["checksums.csv"]["sha256"],
                "redaction_audit_sha256": sha256(audit_path),
                "email_values_removed": package["redaction"]["email_values_removed"],
                "remaining_literal_email_values": 0,
            }
        )
    if sum(record["row_count"] for record in records) != staging["reaction_count"]:
        raise ValueError("staging rows do not add up")
    result = {
        "schema_version": "1.0.0",
        "step_id": "step-11",
        "status": "staging_complete_not_released",
        "staging_run_manifest_sha256": sha256(staging_manifest_path),
        "input_hashes": staging["input_hashes"],
        "corpus_count": staging["corpus_count"],
        "reaction_count": staging["reaction_count"],
        "email_values_removed": staging["email_values_removed"],
        "remaining_literal_email_values": 0,
        "packages": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, output_path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-manifest", required=True, type=Path)
    parser.add_argument("--audit-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = snapshot(args.staging_manifest, args.audit_root, args.output)
    print(json.dumps({key: result[key] for key in ("corpus_count", "reaction_count", "email_values_removed")}, sort_keys=True))


if __name__ == "__main__":
    main()
