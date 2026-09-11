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
"""Stream-redact literal email addresses from a CSV reaction_json column.

The input stays untouched. The output preserves CSV columns, row order, and
non-email JSON content while deleting dict fields or list elements whose scalar
string value is an email address. The optional audit contains no matched value.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

EMAIL = re.compile(r"(?i)^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$")
DROP = object()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def redact(node: Any, path: str, counts: Counter[str]) -> Any:
    """Return a structurally equivalent node with literal emails removed."""
    if isinstance(node, dict):
        result: dict[str, Any] = {}
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else str(key)
            clean = redact(value, child_path, counts)
            if clean is not DROP:
                result[key] = clean
        return result
    if isinstance(node, list):
        result = []
        for value in node:
            clean = redact(value, f"{path}[]", counts)
            if clean is not DROP:
                result.append(clean)
        return result
    if isinstance(node, str) and EMAIL.fullmatch(node):
        counts[path] += 1
        return DROP
    return node


def sanitize(input_path: Path, output_path: Path, audit_path: Path | None) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    row_count = 0
    with input_path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or "reaction_json" not in reader.fieldnames:
            raise ValueError("input CSV must contain a reaction_json column")
        fieldnames = reader.fieldnames
        with output_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for row in reader:
                payload = json.loads(row["reaction_json"])
                clean = redact(payload, "", counts)
                if clean is DROP:
                    raise ValueError("reaction_json root cannot be an email value")
                row["reaction_json"] = json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
                writer.writerow(row)
                row_count += 1

    audit = {
        "schema_version": "1.0.0",
        "input_sha256": sha256(input_path),
        "output_sha256": sha256(output_path),
        "row_count": row_count,
        "fieldnames": fieldnames,
        "email_values_removed": sum(counts.values()),
        "redacted_json_paths": dict(sorted(counts.items())),
        "redaction_policy": "delete_only_literal_email_values",
        "value_retention": "no_email_values_or_source_paths_are_written_to_this_audit",
    }
    if audit_path is not None:
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--audit-json", type=Path)
    args = parser.parse_args()
    audit = sanitize(args.input_csv, args.output_csv, args.audit_json)
    print(json.dumps({"row_count": audit["row_count"], "email_values_removed": audit["email_values_removed"]}))


if __name__ == "__main__":
    main()
