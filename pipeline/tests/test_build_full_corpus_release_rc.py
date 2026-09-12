#!/usr/bin/env python3
"""Clean-room regression test for the full-corpus local RC workflow."""

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
BUILDER_PATH = ROOT / "pipeline/scripts/build_full_corpus_release_rc.py"
VALIDATOR_PATH = ROOT / "pipeline/scripts/validate_full_corpus_release_rc.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = load_module("full_corpus_builder", BUILDER_PATH)
VALIDATOR = load_module("full_corpus_validator", VALIDATOR_PATH)

PHYSICAL_ID = "ord_dataset-00000000000000000000000000000000"
LOGICAL_ID = "physical_00000000000000000000000000000000"
SOURCE_FILE = "data/00/ord_dataset-00000000000000000000000000000000.parquet"
REVISION = "83f971f586f6ad18f358ae4ae99d045e94ed2066"
SOURCE_HASH = "0" * 64


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def write_csv(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


class FullCorpusReleaseCandidateTest(unittest.TestCase):
    def test_builds_and_validates_a_self_contained_fixture_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_files = root / "source-files.csv"
            write_csv(
                source_files,
                ["physical_dataset_id", "upstream_path", "upstream_revision", "source_file_url", "source_sha256", "git_lfs_oid", "size_bytes", "reaction_count", "data_license_id", "verification_status"],
                [{"physical_dataset_id": PHYSICAL_ID, "upstream_path": SOURCE_FILE, "upstream_revision": REVISION, "source_file_url": f"https://github.com/open-reaction-database/ord-data/blob/{REVISION}/{SOURCE_FILE}", "source_sha256": SOURCE_HASH, "git_lfs_oid": SOURCE_HASH, "size_bytes": 1, "reaction_count": 1, "data_license_id": "CC-BY-SA-4.0", "verification_status": "verified"}],
            )
            semantic = root / "semantic.csv"
            write_csv(
                semantic,
                ["logical_dataset_id", "directory_slug", "display_name_en", "display_name_zh", "physical_dataset_ids_json", "physical_source_files_json", "reaction_count", "naming_policy_version"],
                [{"logical_dataset_id": LOGICAL_ID, "directory_slug": "fixture-corpus", "display_name_en": "Fixture Corpus", "display_name_zh": "测试语料", "physical_dataset_ids_json": json.dumps([PHYSICAL_ID]), "physical_source_files_json": json.dumps([SOURCE_FILE]), "reaction_count": 1, "naming_policy_version": "semantic-names-v1"}],
            )
            members = root / "members.csv"
            write_csv(members, ["logical_dataset_id", "physical_dataset_id", "source_file", "reaction_count"], [{"logical_dataset_id": LOGICAL_ID, "physical_dataset_id": PHYSICAL_ID, "source_file": SOURCE_FILE, "reaction_count": 1}])
            staging = root / "staging"
            package = staging / "fixture-corpus"
            package.mkdir(parents=True)
            (package / "reactions.csv").write_text(
                "physical_dataset_id,source_file,reaction_id,row_index,reaction_json\n"
                f"{PHYSICAL_ID},{SOURCE_FILE},fixture:0,0,\"{{\"\"name\"\": \"\"safe\"\"}}\"\n",
                encoding="utf-8",
            )
            write_json(package / "schema.json", {"header": ["physical_dataset_id", "source_file", "reaction_id", "row_index", "reaction_json"], "contract": "pipeline/schemas/csv-contracts.json#corpus_reactions"})
            source_links = {"schema_version": "1.0.0", "logical_dataset_id": LOGICAL_ID, "source_manifest_path": "provenance/source-files.initial.csv", "links": [{"physical_dataset_id": PHYSICAL_ID, "source_file": SOURCE_FILE, "upstream_revision": REVISION, "source_file_url": f"https://github.com/open-reaction-database/ord-data/blob/{REVISION}/{SOURCE_FILE}", "source_sha256": SOURCE_HASH, "git_lfs_oid": SOURCE_HASH, "size_bytes": 1, "reaction_count": 1, "data_license_id": "CC-BY-SA-4.0", "verification_status": "verified"}]}
            write_json(package / "source-links.json", source_links)
            checksum_rows = []
            for role, name in (("reactions", "reactions.csv"), ("schema", "schema.json"), ("source-links", "source-links.json")):
                item = package / name
                checksum_rows.append({"role": role, "path": name, "sha256": sha256(item), "size_bytes": item.stat().st_size})
            write_csv(package / "checksums.csv", ["role", "path", "sha256", "size_bytes"], checksum_rows)
            metadata = {
                "schema_version": "1.0.0", "dataset_kind": "corpus", "dataset_slug": "fixture-corpus", "display_name_en": "Fixture Corpus", "display_name_zh": "测试语料", "logical_dataset_id": LOGICAL_ID,
                "physical_dataset_ids": [PHYSICAL_ID], "source_links_path": "datasets/corpus/fixture-corpus/source-links.json", "license_id": "CC-BY-SA-4.0", "artifact_status": "staged", "readiness_status": "complete_corpus_pending_release_validation", "corpus_row_count": 1,
                "target_id": None, "label": None, "included_count": None, "excluded_count": None,
                "content_artifacts": [{"role": "reactions", "path": "datasets/corpus/fixture-corpus/reactions.csv", "sha256": sha256(package / "reactions.csv"), "size_bytes": (package / "reactions.csv").stat().st_size}, {"role": "schema", "path": "datasets/corpus/fixture-corpus/schema.json", "sha256": sha256(package / "schema.json"), "size_bytes": (package / "schema.json").stat().st_size}, {"role": "checksums", "path": "datasets/corpus/fixture-corpus/checksums.csv", "sha256": sha256(package / "checksums.csv"), "size_bytes": (package / "checksums.csv").stat().st_size}],
                "input_provenance": {"ord_upstream_revision": REVISION, "source_manifest_sha256": sha256(source_files), "semantic_name_policy_version": "semantic-names-v1", "provenance_schema_version": "1.0.0", "pipeline_commit": None},
            }
            write_json(package / "metadata.json", metadata)
            control = root / "control.json"
            write_json(control, {"status": "staging_complete_not_released", "corpus_count": 1, "packages": [{"dataset_slug": "fixture-corpus", "logical_dataset_id": LOGICAL_ID, "row_count": 1, "reaction_sha256": sha256(package / "reactions.csv"), "metadata_sha256": sha256(package / "metadata.json"), "source_links_sha256": sha256(package / "source-links.json"), "checksums_sha256": sha256(package / "checksums.csv")} ]})
            private_sums = root / "private-SHA256SUMS"
            private_lines = []
            for item in sorted(package.iterdir(), key=lambda path: path.name):
                private_lines.append(f"{sha256(item)}  ./fixture-corpus/{item.name}\n")
            private_sums.write_text("".join(private_lines), encoding="utf-8")
            expected_counts = {"physical_sources_referenced": 1, "corpus_packages": 1, "corpus_payload_files": 5, "corpus_payload_bytes": sum(item.stat().st_size for item in package.iterdir()), "reactions": 1}
            candidate = root / "candidate"
            result = BUILDER.build(staging, semantic, members, source_files, control, private_sums, sha256(private_sums), "corpus-staging-step11-4a546010d1aad3ba", ROOT / "pipeline/schemas", ROOT, ROOT / "project-docs/hf-corpus-dataset-card.md", candidate, "v0.2.0-corpus-preview-1", "a" * 40, "2026-09-12T00:00:00Z", root / "build-report.json", expected_counts)
            self.assertTrue((candidate / "SHA256SUMS").is_file())
            self.assertFalse(result["remote_write_attempted"])
            validation = VALIDATOR.validate(candidate, ROOT / "pipeline/schemas", strict_frozen_baseline=False)
            self.assertEqual("local_validation_passed_pending_publication_authorization", validation["status"])
            self.assertEqual(0, validation["blocking_check_failures"])


if __name__ == "__main__":
    unittest.main()
