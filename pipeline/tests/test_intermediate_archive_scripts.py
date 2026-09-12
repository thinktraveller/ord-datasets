#!/usr/bin/env python3
"""Contract tests for the non-duplicating intermediate archive indexers."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "pipeline" / "scripts" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ARCHIVER = load("intermediate_archiver", "archive_intermediate_indices.py")
MODEL_ARCHIVER = load("model_intermediate_archiver", "archive_model_ready_intermediates.py")


class IntermediateArchiveContractTest(unittest.TestCase):
    def test_step16_has_all_required_nonoverlapping_stage_rules(self) -> None:
        self.assertEqual(
            {"00-snapshot-inventory", "01-physical-csv", "02-source-evidence", "03-logical-assembly", "04-field-profiling"},
            set(ARCHIVER.STEP16),
        )
        self.assertTrue(all(rules for rules in ARCHIVER.STEP16.values()))

    def test_step17_routes_every_staged_target_artifact_once(self) -> None:
        self.assertEqual(10, len(MODEL_ARCHIVER.ROUTES))
        self.assertEqual({"05-model-projection", "06-target-adaptation", "07-validation-configs", "08-runs-and-reports"}, set(MODEL_ARCHIVER.ROUTES.values()))
        self.assertEqual("05-model-projection", MODEL_ARCHIVER.ROUTES["dataset.csv"])
        self.assertEqual("06-target-adaptation", MODEL_ARCHIVER.ROUTES["row-map.csv"])
        self.assertEqual("07-validation-configs", MODEL_ARCHIVER.ROUTES["yonod-config.json"])


if __name__ == "__main__":
    unittest.main()
