#!/usr/bin/env python3
"""Regression tests for the isolated model-ready preview RC builder."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "pipeline" / "scripts" / "build_model_ready_preview_rc.py"
SPEC = importlib.util.spec_from_file_location("preview_rc_builder", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

VALIDATOR_SCRIPT = ROOT / "pipeline" / "scripts" / "validate_model_ready_preview_rc.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("preview_rc_validator", VALIDATOR_SCRIPT)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
sys.modules[VALIDATOR_SPEC.name] = VALIDATOR
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)

REVISION = "a" * 40
SOURCE_ID = "ord_dataset-00000000000000000000000000000000"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


class ModelReadyPreviewBuilderTest(unittest.TestCase):
    def test_builds_hash_stable_19_target_rc_without_excluded_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_files = root / "source-files.initial.csv"
            source_header = [
                "physical_dataset_id",
                "upstream_revision",
                "upstream_path",
                "source_file_url",
                "source_sha256",
                "git_lfs_oid",
                "size_bytes",
                "reaction_count",
                "data_license_id",
            ]
            source_rows = []
            for index in range(53):
                identifier = f"ord_dataset-{index:032x}"
                source_file = f"data/00/{identifier}.parquet"
                source_rows.append(
                    {
                        "physical_dataset_id": identifier,
                        "upstream_revision": REVISION,
                        "upstream_path": source_file,
                        "source_file_url": f"https://github.com/open-reaction-database/ord-data/blob/{REVISION}/{source_file}",
                        "source_sha256": f"{index + 1:064x}",
                        "git_lfs_oid": f"{index + 1:064x}",
                        "size_bytes": 1,
                        "reaction_count": 1,
                        "data_license_id": "CC-BY-SA-4.0",
                    }
                )
            write_csv(source_files, source_header, source_rows)
            target_map = root / "semantic-target-map.csv"
            target_header = [
                "target_id",
                "target_slug",
                "display_name_en",
                "display_name_zh",
                "logical_dataset_id",
                "corpus_directory_slug",
                "physical_dataset_ids_json",
                "physical_source_files_json",
                "label_column",
                "label_type",
                "label_unit",
                "included_count",
                "excluded_count",
                "readiness_status",
            ]
            source_file = source_rows[0]["upstream_path"]
            target_rows = []
            for index in range(19):
                target_rows.append(
                    {
                        "target_id": f"target_{index}",
                        "target_slug": f"target-{index:02d}",
                        "display_name_en": f"Target {index}",
                        "display_name_zh": f"目标 {index}",
                        "logical_dataset_id": f"physical_{index % 15:032x}",
                        "corpus_directory_slug": f"reference-{index % 15:02d}",
                        "physical_dataset_ids_json": json.dumps([SOURCE_ID]),
                        "physical_source_files_json": json.dumps([source_file]),
                        "label_column": "yield_percent",
                        "label_type": "reaction_yield_percent",
                        "label_unit": "percent yield",
                        "included_count": 1,
                        "excluded_count": 0,
                        "readiness_status": "active_generated_pending_release_validation",
                    }
                )
            write_csv(target_map, target_header, target_rows)
            staging = root / "staging"
            staging.mkdir()
            control_packages = []
            for target in target_rows:
                directory = staging / str(target["target_slug"])
                directory.mkdir()
                write_json(directory / "audit.jsonl", {"decision": "included"})
                (directory / "dataset.csv").write_text("reaction_key,yield_percent\nfixture:0,1\n", encoding="utf-8")
                (directory / "exclusions.csv").write_text(
                    "reaction_key,physical_dataset_id,source_row_index,label_decision_id,exclusion_reason\n", encoding="utf-8"
                )
                (directory / "row-map.csv").write_text(
                    f"csv_row_number,reaction_key,physical_dataset_id,source_row_index,label_decision_id\n1,fixture:0,{SOURCE_ID},0,decision-0\n",
                    encoding="utf-8",
                )
                write_json(directory / "schema.json", {"type": "object"})
                write_json(directory / "target-build-provenance.json", {"schema_version": "1.0.0"})
                write_json(directory / "yonod-config.json", {"target": target["target_id"]})
                link = {
                    "physical_dataset_id": SOURCE_ID,
                    "source_file": source_file,
                    "upstream_revision": REVISION,
                    "source_file_url": source_rows[0]["source_file_url"],
                    "source_sha256": source_rows[0]["source_sha256"],
                    "git_lfs_oid": source_rows[0]["git_lfs_oid"],
                    "size_bytes": 1,
                    "reaction_count": 1,
                    "data_license_id": "CC-BY-SA-4.0",
                    "verification_status": "verified",
                }
                write_json(
                    directory / "source-links.json",
                    {
                        "schema_version": "1.0.0",
                        "logical_dataset_id": target["logical_dataset_id"],
                        "source_manifest_path": "provenance/source-files.initial.csv",
                        "links": [link],
                    },
                )
                write_json(
                    directory / "metadata.json",
                    {
                        "schema_version": "1.0.0",
                        "dataset_kind": "model-ready",
                        "dataset_slug": target["target_slug"],
                        "display_name_en": target["display_name_en"],
                        "display_name_zh": target["display_name_zh"],
                        "logical_dataset_id": target["logical_dataset_id"],
                        "physical_dataset_ids": [SOURCE_ID],
                        "source_links_path": f"datasets/model-ready/{target['target_slug']}/source-links.json",
                        "license_id": "CC-BY-SA-4.0",
                        "artifact_status": "staged",
                        "readiness_status": target["readiness_status"],
                        "corpus_row_count": 1,
                        "target_id": target["target_id"],
                        "label": {"column": "yield_percent", "type": "reaction_yield_percent", "unit": "percent yield", "policy": "fixture"},
                        "included_count": 1,
                        "excluded_count": 0,
                        "content_artifacts": [{"role": "dataset", "path": f"datasets/model-ready/{target['target_slug']}/dataset.csv", "sha256": None, "size_bytes": 0}],
                        "input_provenance": {"ord_upstream_revision": REVISION, "source_manifest_sha256": "b" * 64, "semantic_name_policy_version": "fixture", "provenance_schema_version": "1.0.0", "pipeline_commit": None},
                    },
                )
                checksum_rows = []
                for role, filename in MODULE.CHECKSUM_FILES.items():
                    item = directory / filename
                    checksum_rows.append({"role": role, "path": filename, "sha256": sha256(item), "size_bytes": item.stat().st_size})
                write_csv(directory / "checksums.csv", ["role", "path", "sha256", "size_bytes"], checksum_rows)
                control_packages.append(
                    {
                        "target_slug": target["target_slug"],
                        "target_id": target["target_id"],
                        "logical_dataset_id": target["logical_dataset_id"],
                        "readiness_status": target["readiness_status"],
                        "included_count": 1,
                        "excluded_count": 0,
                        "artifacts": {item.name: {"sha256": sha256(item), "size_bytes": item.stat().st_size} for item in directory.iterdir()},
                    }
                )
            control = root / "target-control.json"
            write_json(control, {"status": "staging_complete_not_released", "packages": control_packages})

            first = MODULE.build(
                staging,
                target_map,
                control,
                source_files,
                ROOT / "pipeline" / "schemas",
                ROOT,
                root / "rc-one",
                "v0.0.0-model-ready-preview-test",
                "c" * 40,
                "2026-09-12T00:00:00Z",
                root / "first-report.json",
            )
            second = MODULE.build(
                staging,
                target_map,
                control,
                source_files,
                ROOT / "pipeline" / "schemas",
                ROOT,
                root / "rc-two",
                "v0.0.0-model-ready-preview-test",
                "c" * 40,
                "2026-09-12T00:00:00Z",
                root / "second-report.json",
            )
            candidate = root / "rc-one"
            self.assertEqual(190, first["payload"]["target_payload_files"])
            self.assertEqual(first["root_sha256"], second["root_sha256"])
            self.assertFalse((candidate / "datasets" / "corpus").exists())
            self.assertFalse(list(candidate.rglob("*.parquet")))
            self.assertEqual(19, len(list((candidate / "datasets" / "model-ready").iterdir())))
            with (candidate / "datasets" / "catalog.csv").open(encoding="utf-8", newline="") as handle:
                self.assertEqual(19, len(list(csv.DictReader(handle))))
            validation = VALIDATOR.validate(candidate, ROOT / "pipeline" / "schemas", strict_frozen_baseline=False)
            self.assertEqual("local_validation_passed_pending_owner_gates", validation["status"])
            self.assertEqual(0, validation["blocking_check_failures"])


if __name__ == "__main__":
    unittest.main()
