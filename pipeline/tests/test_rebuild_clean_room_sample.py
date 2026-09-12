#!/usr/bin/env python3
"""Smoke-test the public-source clean-room adapter without a network fixture."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pyarrow as pa
import pyarrow.parquet as pq
from ord_schema.proto import reaction_pb2

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "pipeline" / "scripts" / "rebuild_clean_room_sample.py"
SPEC = importlib.util.spec_from_file_location("clean_room_rebuilder", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

PHYSICAL_ID = "ord_dataset-00000000000000000000000000000000"
LOGICAL_ID = "physical_00000000000000000000000000000000"
SOURCE_FILE = "data/00/ord_dataset-00000000000000000000000000000000.parquet"
REVISION = "83f971f586f6ad18f358ae4ae99d045e94ed2066"
TARGET_ID = "ahneman_yield_percent"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fixture_parquet(path: Path) -> None:
    reaction_ids = []
    reactions = []
    # Deliberately write reverse reaction-ID order.  The standardized target
    # contract must sort by reaction ID rather than preserve Parquet order.
    for number, yield_percent in ((2, 87.5), (1, 12.5)):
        reaction = reaction_pb2.Reaction(reaction_id=f"ord-fixture-{number}")
        reaction.provenance.record_created.person.email = "fixture@example.invalid"
        reaction.inputs["reactant"].components.add(
            reaction_role=reaction_pb2.ReactionRole.REACTANT
        ).identifiers.add(type=reaction_pb2.CompoundIdentifier.SMILES, value="OCC")
        reaction.conditions.temperature.setpoint.value = 298.15
        reaction.conditions.temperature.setpoint.units = reaction_pb2.Temperature.KELVIN
        outcome = reaction.outcomes.add()
        outcome.reaction_time.value = 1.5
        outcome.reaction_time.units = reaction_pb2.Time.HOUR
        product = outcome.products.add()
        product.identifiers.add(type=reaction_pb2.CompoundIdentifier.SMILES, value="O=CC")
        measurement = product.measurements.add()
        measurement.type = reaction_pb2.ProductMeasurement.YIELD
        measurement.percentage.value = yield_percent
        reaction_ids.append(reaction.reaction_id)
        reactions.append(reaction.SerializeToString())
    pq.write_table(pa.table({"reaction_id": pa.array(reaction_ids), "reaction": pa.array(reactions, type=pa.binary())}), path)


class CleanRoomRebuilderTest(unittest.TestCase):
    def test_rebuilds_a_hash_stable_physical_corpus_and_target_without_local_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_parquet = root / "public-fixture.parquet"
            fixture_parquet(source_parquet)
            source_hash = sha256(source_parquet)
            source_manifest = root / "source-files.csv"
            write_csv(
                source_manifest,
                [
                    "source_file_id",
                    "physical_dataset_id",
                    "upstream_repo_url",
                    "upstream_revision",
                    "upstream_path",
                    "source_file_url",
                    "direct_download_url",
                    "source_sha256",
                    "git_lfs_oid",
                    "size_bytes",
                    "reaction_count",
                    "dataset_name",
                    "dataset_description",
                    "data_license_id",
                    "source_present",
                    "hash_matches_lfs",
                    "verification_status",
                ],
                [
                    {
                        "source_file_id": PHYSICAL_ID,
                        "physical_dataset_id": PHYSICAL_ID,
                        "upstream_repo_url": "https://github.com/open-reaction-database/ord-data.git",
                        "upstream_revision": REVISION,
                        "upstream_path": SOURCE_FILE,
                        "source_file_url": f"https://github.com/open-reaction-database/ord-data/blob/{REVISION}/{SOURCE_FILE}",
                        "direct_download_url": "",
                        "source_sha256": source_hash,
                        "git_lfs_oid": source_hash,
                        "size_bytes": source_parquet.stat().st_size,
                        "reaction_count": 2,
                        "dataset_name": "Fixture",
                        "dataset_description": "Fixture",
                        "data_license_id": "CC-BY-SA-4.0",
                        "source_present": "true",
                        "hash_matches_lfs": "true",
                        "verification_status": "verified",
                    }
                ],
            )
            semantic_map = root / "semantic-map.csv"
            write_csv(
                semantic_map,
                [
                    "logical_dataset_id",
                    "directory_slug",
                    "display_name_en",
                    "display_name_zh",
                    "aliases_json",
                    "relationship",
                    "member_count",
                    "reaction_count",
                    "physical_dataset_ids_json",
                    "physical_source_files_json",
                    "source_dois_json",
                    "upstream_source_ids_json",
                    "source_evidence_types_json",
                    "naming_evidence",
                    "semantic_name_status",
                    "naming_policy_version",
                    "planned_dataset_path",
                ],
                [
                    {
                        "logical_dataset_id": LOGICAL_ID,
                        "directory_slug": "fixture-corpus",
                        "display_name_en": "Fixture Corpus",
                        "display_name_zh": "测试语料",
                        "aliases_json": json.dumps([LOGICAL_ID]),
                        "relationship": "independent",
                        "member_count": 1,
                        "reaction_count": 2,
                        "physical_dataset_ids_json": json.dumps([PHYSICAL_ID]),
                        "physical_source_files_json": json.dumps([SOURCE_FILE]),
                        "source_dois_json": "[]",
                        "upstream_source_ids_json": "[]",
                        "source_evidence_types_json": "[]",
                        "naming_evidence": "fixture",
                        "semantic_name_status": "approved_from_frozen_metadata",
                        "naming_policy_version": "semantic-names-v1",
                        "planned_dataset_path": "datasets/corpus/fixture-corpus",
                    }
                ],
            )
            members = root / "members.csv"
            write_csv(
                members,
                ["logical_dataset_id", "physical_dataset_id", "source_file", "reaction_count", "relationship", "source_file_url", "source_sha256", "upstream_revision"],
                [
                    {
                        "logical_dataset_id": LOGICAL_ID,
                        "physical_dataset_id": PHYSICAL_ID,
                        "source_file": SOURCE_FILE,
                        "reaction_count": 2,
                        "relationship": "independent",
                        "source_file_url": f"https://github.com/open-reaction-database/ord-data/blob/{REVISION}/{SOURCE_FILE}",
                        "source_sha256": source_hash,
                        "upstream_revision": REVISION,
                    }
                ],
            )
            target_map = root / "target-map.csv"
            write_csv(
                target_map,
                [
                    "target_id",
                    "target_slug",
                    "display_name_en",
                    "display_name_zh",
                    "logical_dataset_id",
                    "physical_dataset_ids_json",
                    "physical_source_files_json",
                    "label_column",
                    "label_type",
                    "label_unit",
                    "target_adapter",
                    "label_policy",
                    "included_count",
                    "excluded_count",
                    "source_count",
                    "readiness_status",
                    "naming_policy_version",
                ],
                [
                    {
                        "target_id": TARGET_ID,
                        "target_slug": "fixture-yield-percent",
                        "display_name_en": "Fixture Yield (%)",
                        "display_name_zh": "测试产率（%）",
                        "logical_dataset_id": LOGICAL_ID,
                        "physical_dataset_ids_json": json.dumps([PHYSICAL_ID]),
                        "physical_source_files_json": json.dumps([SOURCE_FILE]),
                        "label_column": "yield_percent",
                        "label_type": "reaction_yield_percent",
                        "label_unit": "percent yield",
                        "target_adapter": "generic",
                        "label_policy": "unique_structured_scalar_no_aggregation",
                        "included_count": 2,
                        "excluded_count": 0,
                        "source_count": 2,
                        "readiness_status": "active_generated_pending_release_validation",
                        "naming_policy_version": "semantic-target-names-v1",
                    }
                ],
            )

            def fake_download(source: dict[str, str], download_root: Path, timeout_seconds: int) -> dict[str, object]:
                del timeout_seconds
                destination = download_root / f"{source['physical_dataset_id']}.parquet"
                shutil.copyfile(source_parquet, destination)
                return {
                    "physical_dataset_id": source["physical_dataset_id"],
                    "raw_lfs_pointer_url": "https://raw.githubusercontent.com/fixture/pointer",
                    "lfs_batch_endpoint": "https://github.com/fixture.git/info/lfs/objects/batch",
                    "lfs_batch_protocol": "basic",
                    "ephemeral_download_action_url_persisted": False,
                    "source_sha256": sha256(destination),
                    "size_bytes": destination.stat().st_size,
                    "path": destination,
                }

            def rebuild(suffix: str) -> dict[str, object]:
                with mock.patch.object(MODULE, "download_lfs_source", side_effect=fake_download):
                    return MODULE.run(
                        source_manifest,
                        semantic_map,
                        members,
                        target_map,
                        ROOT / "pipeline" / "schemas",
                        PHYSICAL_ID,
                        TARGET_ID,
                        root / f"downloads-{suffix}",
                        root / f"output-{suffix}",
                        root / f"report-{suffix}.json",
                    )

            first = rebuild("one")
            second = rebuild("two")
            self.assertEqual("complete", first["status"])
            self.assertEqual(first["reproducibility"]["output_root_sha256"], second["reproducibility"]["output_root_sha256"])
            self.assertEqual(2, first["target"]["included_count"])
            corpus = root / "output-one" / "datasets" / "corpus" / "fixture-corpus" / "reactions.csv"
            self.assertNotIn("fixture@example.invalid", corpus.read_text(encoding="utf-8"))
            dataset = root / "output-one" / "datasets" / "model-ready" / "fixture-yield-percent" / "dataset.csv"
            with dataset.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(2, len(rows))
            self.assertEqual("CCO", rows[0]["reactant-1"])
            self.assertEqual("CC=O", rows[0]["product"])
            self.assertEqual("12.5", rows[0]["yield_percent"])
            self.assertEqual("87.5", rows[1]["yield_percent"])


if __name__ == "__main__":
    unittest.main()
