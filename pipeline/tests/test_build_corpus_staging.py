#!/usr/bin/env python3
"""Small clean-room test for corpus staging, metadata, and literal-email removal."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "pipeline" / "scripts" / "build_corpus_staging.py"
SPEC = importlib.util.spec_from_file_location("corpus_builder", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

PHYSICAL_ID = "ord_dataset-00000000000000000000000000000000"
LOGICAL_ID = "physical_00000000000000000000000000000000"
SOURCE_FILE = "data/00/ord_dataset-00000000000000000000000000000000.parquet"
REVISION = "83f971f586f6ad18f358ae4ae99d045e94ed2066"
HASH = "0" * 64


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class CorpusBuilderTest(unittest.TestCase):
    def test_stages_a_sanitized_corpus_with_pinned_source_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_root = root / "logical-tables"
            source_csv = source_root / f"logical_dataset_id={LOGICAL_ID}" / "reactions.csv"
            write_csv(
                source_csv,
                MODULE.CORPUS_HEADER,
                [{"physical_dataset_id": PHYSICAL_ID, "source_file": SOURCE_FILE, "reaction_id": "ord-test", "row_index": 0, "reaction_json": json.dumps({"provenance": {"person": {"email": "test@example.invalid", "name": "Test"}}})}],
            )
            semantic_map = root / "semantic.csv"
            write_csv(
                semantic_map,
                ["logical_dataset_id", "directory_slug", "display_name_en", "display_name_zh", "physical_dataset_ids_json", "physical_source_files_json", "reaction_count", "naming_policy_version"],
                [{"logical_dataset_id": LOGICAL_ID, "directory_slug": "test-corpus", "display_name_en": "Test Corpus", "display_name_zh": "测试语料", "physical_dataset_ids_json": json.dumps([PHYSICAL_ID]), "physical_source_files_json": json.dumps([SOURCE_FILE]), "reaction_count": 1, "naming_policy_version": "semantic-names-v1"}],
            )
            members = root / "members.csv"
            write_csv(members, ["logical_dataset_id", "physical_dataset_id", "source_file", "reaction_count"], [{"logical_dataset_id": LOGICAL_ID, "physical_dataset_id": PHYSICAL_ID, "source_file": SOURCE_FILE, "reaction_count": 1}])
            sources = root / "sources.csv"
            write_csv(
                sources,
                ["physical_dataset_id", "upstream_path", "upstream_revision", "source_file_url", "source_sha256", "git_lfs_oid", "size_bytes", "reaction_count", "data_license_id", "verification_status"],
                [{"physical_dataset_id": PHYSICAL_ID, "upstream_path": SOURCE_FILE, "upstream_revision": REVISION, "source_file_url": f"https://github.com/open-reaction-database/ord-data/blob/{REVISION}/{SOURCE_FILE}", "source_sha256": HASH, "git_lfs_oid": HASH, "size_bytes": 1, "reaction_count": 1, "data_license_id": "CC-BY-SA-4.0", "verification_status": "verified"}],
            )
            output_root = root / "output"
            summary = MODULE.build(source_root, semantic_map, members, sources, output_root, root / "audits", root / "run.json", ROOT / "pipeline" / "schemas", expected_corpus_count=1, expected_reaction_count=1, expected_physical_count=1)
            self.assertEqual(1, summary["reaction_count"])
            staged = output_root / "test-corpus"
            with (staged / "reactions.csv").open(encoding="utf-8", newline="") as handle:
                output_row = next(csv.DictReader(handle))
            self.assertNotIn("example.invalid", output_row["reaction_json"])
            links = json.loads((staged / "source-links.json").read_text(encoding="utf-8"))
            self.assertEqual(f"https://github.com/open-reaction-database/ord-data/blob/{REVISION}/{SOURCE_FILE}", links["links"][0]["source_file_url"])
            self.assertTrue((staged / "metadata.json").is_file())
            self.assertTrue((staged / "checksums.csv").is_file())


if __name__ == "__main__":
    unittest.main()
