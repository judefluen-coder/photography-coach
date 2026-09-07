#!/usr/bin/env python3
"""Tests for the visual benchmark answer-key alignment audit."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import benchmark_annotation_audit as audit


class AnnotationAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.run = self.root / "run"
        self.run.mkdir()
        self.image = self.run / "image.jpg"
        self.image.write_bytes(b"image-bytes")
        self.cases = self.root / "cases.jsonl"
        self.cases.write_text(
            json.dumps(
                {
                    "id": "bench-001",
                    "must_notice": ["left hand touches cup", "right edge retains space"],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (self.run / "blind-inputs.jsonl").write_text(
            json.dumps(
                {
                    "case_id": "bench-001",
                    "image_path": str(self.image),
                    "image_sha256": audit.file_sha256(self.image),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.audit_path = self.run / "annotation-audit.jsonl"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def complete_row(self) -> dict[str, object]:
        row = json.loads(self.audit_path.read_text(encoding="utf-8").splitlines()[0])
        row.update(
            {
                "reviewer_id": "clean-context-visual-reviewer",
                "image_key_alignment": True,
                "observation_support": [True, True],
                "visible_anchors_checked": ["left hand", "right frame edge"],
            }
        )
        self.audit_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
        return row

    def test_completed_audit_passes(self) -> None:
        with patch.object(audit, "CASES_PATH", self.cases):
            self.assertEqual(audit.init_audit(self.run, self.audit_path), 0)
            self.complete_row()
            self.assertEqual(audit.validate_audit(self.run, self.audit_path), [])

    def test_unsupported_observation_fails(self) -> None:
        with patch.object(audit, "CASES_PATH", self.cases):
            self.assertEqual(audit.init_audit(self.run, self.audit_path), 0)
            row = self.complete_row()
            row["observation_support"] = [True, False]
            self.audit_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            errors = audit.validate_audit(self.run, self.audit_path)
        self.assertTrue(any("every must_notice item needs visible support" in error for error in errors))

    def test_image_change_invalidates_audit(self) -> None:
        with patch.object(audit, "CASES_PATH", self.cases):
            self.assertEqual(audit.init_audit(self.run, self.audit_path), 0)
            self.complete_row()
            self.image.write_bytes(b"changed-image")
            errors = audit.validate_audit(self.run, self.audit_path)
        self.assertTrue(any("image changed after annotation audit" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
