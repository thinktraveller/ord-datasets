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
"""Build the 41-corpus plus 19-target public catalog from staged manifests."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def build(corpus_map: Path, target_map: Path, corpus_stage: Path, target_stage: Path, schema_path: Path, csv_path: Path, json_path: Path) -> dict[str, int]:
    if csv_path.exists() or json_path.exists():
        raise FileExistsError("refusing to overwrite catalog")
    corpus = rows(corpus_map); targets = rows(target_map)
    cstage = {row["dataset_slug"]: row for row in load(corpus_stage)["packages"]}
    tstage = {row["target_slug"]: row for row in load(target_stage)["packages"]}
    if len(corpus) != len(cstage) != 41 or len(targets) != len(tstage) != 19:
        raise ValueError("catalog inputs do not have the expected 41 corpus / 19 target records")
    records = []
    for row in corpus:
        slug = row["directory_slug"]; stage = cstage[slug]
        records.append({"schema_version": "1.0.0", "record_type": "corpus", "dataset_slug": slug, "display_name_en": row["display_name_en"], "display_name_zh": row["display_name_zh"], "logical_dataset_id": row["logical_dataset_id"], "physical_dataset_ids": json.loads(row["physical_dataset_ids_json"]), "physical_source_files": json.loads(row["physical_source_files_json"]), "target_id": None, "label_type": None, "label_unit": None, "readiness_status": "complete_corpus_pending_release_validation", "artifact_status": "staged", "license_id": "CC-BY-SA-4.0", "row_count": int(row["reaction_count"]), "content_sha256": stage["reaction_sha256"], "release_path": f"datasets/corpus/{slug}", "metadata_path": f"datasets/corpus/{slug}/metadata.json", "source_links_path": f"datasets/corpus/{slug}/source-links.json"})
    for row in targets:
        slug = row["target_slug"]; stage = tstage[slug]
        records.append({"schema_version": "1.0.0", "record_type": "model-ready", "dataset_slug": slug, "display_name_en": row["display_name_en"], "display_name_zh": row["display_name_zh"], "logical_dataset_id": row["logical_dataset_id"], "physical_dataset_ids": json.loads(row["physical_dataset_ids_json"]), "physical_source_files": json.loads(row["physical_source_files_json"]), "target_id": row["target_id"], "label_type": row["label_type"], "label_unit": row["label_unit"], "readiness_status": row["readiness_status"], "artifact_status": "staged", "license_id": "CC-BY-SA-4.0", "row_count": int(row["included_count"]), "content_sha256": stage["artifacts"]["dataset.csv"]["sha256"], "release_path": f"datasets/model-ready/{slug}", "metadata_path": f"datasets/model-ready/{slug}/metadata.json", "source_links_path": f"datasets/model-ready/{slug}/source-links.json"})
    validator = Draft202012Validator(load(schema_path))
    for record in records: validator.validate(record)
    records.sort(key=lambda r: (r["record_type"], r["dataset_slug"]))
    json_doc = {"schema_version": "1.0.0", "status": "staging_index_not_released", "corpus_count": 41, "model_ready_target_count": 19, "records": records}
    write_json(json_path, json_doc)
    header = ["record_type", "dataset_slug", "display_name_en", "display_name_zh", "logical_dataset_id", "physical_dataset_ids_json", "physical_source_files_json", "target_id", "label_type", "label_unit", "readiness_status", "artifact_status", "license_id", "row_count", "content_sha256", "release_path", "metadata_path", "source_links_path"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n"); writer.writeheader()
        for r in records:
            writer.writerow({"record_type": r["record_type"], "dataset_slug": r["dataset_slug"], "display_name_en": r["display_name_en"], "display_name_zh": r["display_name_zh"], "logical_dataset_id": r["logical_dataset_id"], "physical_dataset_ids_json": json.dumps(r["physical_dataset_ids"], ensure_ascii=False), "physical_source_files_json": json.dumps(r["physical_source_files"], ensure_ascii=False), **{key: "" if r[key] is None else r[key] for key in header[7:]}})
    return {"corpus_count": 41, "model_ready_target_count": 19, "records": len(records)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus-map", required=True, type=Path); p.add_argument("--target-map", required=True, type=Path)
    p.add_argument("--corpus-stage", required=True, type=Path); p.add_argument("--target-stage", required=True, type=Path)
    p.add_argument("--schema", required=True, type=Path); p.add_argument("--csv", required=True, type=Path); p.add_argument("--json", required=True, type=Path)
    a = p.parse_args(); print(json.dumps(build(a.corpus_map, a.target_map, a.corpus_stage, a.target_stage, a.schema, a.csv, a.json), sort_keys=True))


if __name__ == "__main__": main()
