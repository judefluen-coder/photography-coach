#!/usr/bin/env python3
"""Tests for the frozen coaching-protocol fingerprint surface."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from protocol_fingerprint import PROTOCOL_RELATIVE_PATHS, protocol_sha256


class ProtocolFingerprintTests(unittest.TestCase):
    def test_blind_writer_prompt_and_batch_validator_are_fingerprinted(self) -> None:
        self.assertIn(Path("references/blind-evaluator-prompt.md"), PROTOCOL_RELATIVE_PATHS)
        self.assertIn(Path("scripts/validate_blind_responses.py"), PROTOCOL_RELATIVE_PATHS)

    def test_changing_any_fingerprinted_file_changes_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in PROTOCOL_RELATIVE_PATHS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"frozen:{relative}\n", encoding="utf-8")
            before = protocol_sha256(root)
            target = root / "references" / "blind-evaluator-prompt.md"
            target.write_text("changed blind instructions\n", encoding="utf-8")
            self.assertNotEqual(before, protocol_sha256(root))


if __name__ == "__main__":
    unittest.main()
