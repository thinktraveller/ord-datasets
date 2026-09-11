#!/usr/bin/env python3
"""Regression test for the value-redacting reaction JSON sanitizer."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "sanitize_reaction_json_csv.py"
SPEC = importlib.util.spec_from_file_location("sanitizer", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SanitizerTest(unittest.TestCase):
    def test_removes_only_literal_email_values_and_preserves_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.csv"
            output = root / "output.csv"
            audit_path = root / "audit.json"
            original = {
                "provenance": {
                    "record_created": {"person": {"name": "Ada", "email": "ada@example.invalid"}},
                    "record_modified": [
                        {"person": {"name": "person@example.invalid"}},
                        {"person": {"name": "Grace"}},
                    ],
                },
                "identifiers": ["safe-value", "list@example.invalid"],
            }
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["reaction_id", "reaction_json"], lineterminator="\n")
                writer.writeheader()
                writer.writerow({"reaction_id": "r1", "reaction_json": json.dumps(original)})

            audit = MODULE.sanitize(source, output, audit_path)
            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(["reaction_id", "reaction_json"], list(rows[0]))
            self.assertEqual("r1", rows[0]["reaction_id"])
            clean = json.loads(rows[0]["reaction_json"])
            self.assertEqual("Ada", clean["provenance"]["record_created"]["person"]["name"])
            self.assertNotIn("email", clean["provenance"]["record_created"]["person"])
            self.assertNotIn("name", clean["provenance"]["record_modified"][0]["person"])
            self.assertEqual(["safe-value"], clean["identifiers"])
            self.assertEqual(3, audit["email_values_removed"])
            self.assertNotIn("example.invalid", audit_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
