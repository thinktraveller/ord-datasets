#!/usr/bin/env python3
"""Regression test for release-contract schemas and fixtures."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_release_contracts.py"
SPEC = importlib.util.spec_from_file_location("release_contracts", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ReleaseContractTest(unittest.TestCase):
    def test_positive_and_negative_contract_fixtures(self) -> None:
        summary = MODULE.run_validation()
        self.assertEqual(10, summary["indexed_contracts"])
        self.assertEqual(12, summary["valid_fixtures"])
        self.assertEqual(4, summary["invalid_fixtures"])


if __name__ == "__main__":
    unittest.main()
