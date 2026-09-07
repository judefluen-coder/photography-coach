#!/usr/bin/env python3
"""Tests for the non-verdict image integrity probe."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from analyze_image_integrity import analyze


class IntegrityProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def save(self, name: str, image: Image.Image) -> Path:
        path = self.root / name
        image.save(path)
        return path

    def families(self, path: Path) -> set[str]:
        return {item["family"] for item in analyze(path)["signals"]}

    def test_near_black_field_routes_shadow_review(self) -> None:
        path = self.save("black.png", Image.new("RGB", (96, 96), (2, 2, 2)))
        self.assertIn("暗部", self.families(path))

    def test_near_white_field_routes_highlight_review(self) -> None:
        path = self.save("white.png", Image.new("RGB", (96, 96), (253, 253, 253)))
        self.assertIn("高光", self.families(path))

    def test_saturated_field_routes_color_review(self) -> None:
        path = self.save("red.png", Image.new("RGB", (96, 96), (250, 5, 5)))
        self.assertIn("色彩", self.families(path))

    def test_metrics_are_serializable_primitives(self) -> None:
        path = self.save("gray.png", Image.new("RGB", (96, 64), (128, 128, 128)))
        result = analyze(path)
        self.assertEqual(result["image"]["original_width"], 96)
        self.assertIsInstance(result["metrics"]["shadow"]["deep_shadow_fraction"], float)
        self.assertIn("interpretation_rule", result)


if __name__ == "__main__":
    unittest.main()
