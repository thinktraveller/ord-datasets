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
"""Validate frozen release-contract schemas and their positive/negative fixtures."""

from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).parents[2]
SCHEMA_DIR = ROOT / "pipeline" / "schemas"
FIXTURE_PATH = ROOT / "pipeline" / "tests" / "fixtures" / "release-contracts.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def assert_schema_index(index: dict[str, Any]) -> list[str]:
    names: list[str] = []
    if index["schema_family_version"] != "1.0.0":
        raise AssertionError("schema family version must be 1.0.0 during this frozen build step")
    for contract in index["contracts"]:
        schema_path = SCHEMA_DIR / contract["file"]
        if not schema_path.is_file():
            raise AssertionError(f"schema index references missing file: {contract['file']}")
        schema = load_json(schema_path)
        if contract["format"] == "json":
            Draft202012Validator.check_schema(schema)
        names.append(contract["file"])
    return names


def assert_csv_contracts(contract: dict[str, Any]) -> None:
    if contract["schema_version"] != "1.0.0":
        raise AssertionError("CSV contract version mismatch")
    for name, definition in contract["contracts"].items():
        header = definition["header"]
        if len(header) != len(set(header)):
            raise AssertionError(f"duplicate CSV header in {name}")
        if set(header) != set(definition["columns"]):
            raise AssertionError(f"CSV columns and header disagree in {name}")
    corpus = contract["contracts"]["corpus_reactions"]
    if corpus["header"][:4] != ["physical_dataset_id", "source_file", "reaction_id", "row_index"]:
        raise AssertionError("corpus lineage columns must be the first four columns")


def assert_pinned_source_links(instance: dict[str, Any]) -> None:
    for link in instance["links"]:
        url = link["source_file_url"]
        if "/blob/main/" in url or link["upstream_revision"] not in url:
            raise AssertionError("source link is not commit pinned")
        if link["source_file"] not in url:
            raise AssertionError("source URL does not name its source file")


def assert_source_manifest_match(instance: dict[str, Any]) -> None:
    manifest_path = ROOT / instance["source_manifest_path"]
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        sources = {row["physical_dataset_id"]: row for row in csv.DictReader(handle)}
    for link in instance["links"]:
        frozen = sources.get(link["physical_dataset_id"])
        if frozen is None:
            raise AssertionError("source link names an unknown frozen physical dataset")
        for field, frozen_field in (
            ("source_file", "upstream_path"),
            ("upstream_revision", "upstream_revision"),
            ("source_file_url", "source_file_url"),
            ("source_sha256", "source_sha256"),
            ("git_lfs_oid", "git_lfs_oid"),
            ("data_license_id", "data_license_id"),
        ):
            if link[field] != frozen[frozen_field]:
                raise AssertionError(f"source link disagrees with frozen manifest: {field}")
        if link["size_bytes"] != int(frozen["size_bytes"]) or link["reaction_count"] != int(frozen["reaction_count"]):
            raise AssertionError("source link size or reaction count disagrees with frozen manifest")


def assert_fixture_lineage(fixtures: dict[str, Any]) -> None:
    valid = fixtures["valid"]
    source_links = valid["source-links.schema.json"][0]
    source_ids = {link["physical_dataset_id"] for link in source_links["links"]}
    logical_id = source_links["logical_dataset_id"]
    for catalog in valid["catalog-record.schema.json"]:
        if catalog["logical_dataset_id"] != logical_id or set(catalog["physical_dataset_ids"]) != source_ids:
            raise AssertionError("catalog fixture does not preserve the source-link physical-to-logical relationship")
    for metadata in valid["dataset-metadata.schema.json"]:
        if metadata["logical_dataset_id"] != logical_id or set(metadata["physical_dataset_ids"]) != source_ids:
            raise AssertionError("metadata fixture does not preserve the source-link physical-to-logical relationship")
    target_records = [record for record in valid["catalog-record.schema.json"] if record["record_type"] == "model-ready"]
    if len(target_records) != 1 or target_records[0]["target_id"] != "shields_yield_percent":
        raise AssertionError("fixture must express a target-specific projection")


def run_validation() -> dict[str, int]:
    index = load_json(SCHEMA_DIR / "schema-index.json")
    indexed_files = assert_schema_index(index)
    assert_csv_contracts(load_json(SCHEMA_DIR / "csv-contracts.json"))
    fixtures = load_json(FIXTURE_PATH)
    assert_fixture_lineage(fixtures)
    checker = FormatChecker()
    valid_count = 0
    invalid_count = 0
    for schema_name, instances in fixtures["valid"].items():
        validator = Draft202012Validator(load_json(SCHEMA_DIR / schema_name), format_checker=checker)
        for instance in instances:
            validator.validate(instance)
            if schema_name == "source-links.schema.json":
                assert_pinned_source_links(instance)
                assert_source_manifest_match(instance)
            valid_count += 1
    for schema_name, instances in fixtures["invalid"].items():
        validator = Draft202012Validator(load_json(SCHEMA_DIR / schema_name), format_checker=checker)
        for instance in instances:
            if not list(validator.iter_errors(instance)):
                raise AssertionError(f"invalid fixture unexpectedly accepted: {schema_name}")
            invalid_count += 1
    expected_json_schemas = {contract["file"] for contract in index["contracts"] if contract["format"] == "json"}
    if expected_json_schemas != set(fixtures["valid"]):
        raise AssertionError("each JSON schema must have a valid fixture")
    return {"indexed_contracts": len(indexed_files), "valid_fixtures": valid_count, "invalid_fixtures": invalid_count}


def main() -> None:
    print(json.dumps(run_validation(), sort_keys=True))


if __name__ == "__main__":
    main()
