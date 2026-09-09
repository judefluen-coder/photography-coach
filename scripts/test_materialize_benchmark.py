#!/usr/bin/env python3
"""Unit tests for deterministic blind-benchmark transformations."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from materialize_benchmark import (
    apply_recipe,
    load_verified_resume_items,
    mean_absolute_difference,
    write_manifest_atomic,
)


class TransformationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.image = Image.new("RGB", (240, 160))
        pixels = self.image.load()
        for y in range(self.image.height):
            for x in range(self.image.width):
                pixels[x, y] = (x % 256, y % 256, (x + y) % 256)

    def assert_changed(self, operation: str, parameters: dict[str, object]) -> Image.Image:
        result = apply_recipe(
            self.image,
            {"operation": operation, "parameters": parameters},
        )
        self.assertEqual(result.size, self.image.size)
        self.assertGreater(mean_absolute_difference(self.image, result), 1)
        return result

    def test_crop_pressure(self) -> None:
        self.assert_changed(
            "crop_pressure",
            {"left_pct": .12, "right_pct": .18, "top_pct": .08, "bottom_pct": .10},
        )

    def test_shadow_crush(self) -> None:
        self.assert_changed("shadow_crush", {"black_point": .24, "gamma": 1.55})

    def test_highlight_clip(self) -> None:
        self.assert_changed("highlight_clip", {"exposure_stops": 1.45, "clip_point": .9})

    def test_color_excess(self) -> None:
        self.assert_changed(
            "color_excess",
            {"saturation": 1.95, "red_gain": 1.12, "green_gain": 1.03, "blue_gain": .82},
        )

    def test_tilt_and_crop_removes_fill_corners(self) -> None:
        result = self.assert_changed(
            "tilt_and_crop", {"angle_degrees": 4.8, "resample": "bicubic"}
        )
        self.assertNotEqual(result.getpixel((0, 0)), (0, 0, 0))
        self.assertNotEqual(result.getpixel((result.width - 1, result.height - 1)), (0, 0, 0))

    def test_detail_damage(self) -> None:
        self.assert_changed(
            "detail_damage",
            {
                "downsample_factor": .18,
                "gaussian_blur_radius": 1.1,
                "jpeg_quality": 28,
                "sharpen_amount": 1.8,
            },
        )


class ResumeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.output = Path(self.temporary.name)
        self.image_path = self.output / "v4-001.jpg"
        Image.new("RGB", (32, 24), (20, 40, 60)).save(self.image_path)
        self.case = {
            "id": "v4-001",
            "quality_band": "ordinary",
            "genre": "landscape",
            "source_page": "https://example.test/source",
            "image_url": "https://example.test/original.jpg",
            "preview_url": "https://example.test/preview.jpg",
            "source_sha1": "a" * 40,
            "variant_recipe": None,
        }
        self.item = {
            "id": "v4-001",
            "quality_band": self.case["quality_band"],
            "genre": self.case["genre"],
            "source_page": self.case["source_page"],
            "download_url": self.case["image_url"],
            "source_sha1": self.case["source_sha1"],
            "variant_recipe": None,
            "output_path": str(self.image_path),
            "output_sha256": hashlib.sha256(self.image_path.read_bytes()).hexdigest(),
            "output_width": 32,
            "output_height": 24,
        }
        self.manifest = self.output / "manifest.json"
        write_manifest_atomic(self.manifest, [self.item])

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_verified_resume_item_is_reused(self) -> None:
        verified = load_verified_resume_items(
            self.manifest, [self.case], self.output, True,
        )
        self.assertEqual(list(verified), ["v4-001"])

    def test_tampered_resume_output_fails(self) -> None:
        self.image_path.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            load_verified_resume_items(self.manifest, [self.case], self.output, True)

    def test_stale_resume_source_page_fails(self) -> None:
        stale = dict(self.item)
        stale["source_page"] = "https://example.test/old-source"
        write_manifest_atomic(self.manifest, [stale])
        with self.assertRaisesRegex(ValueError, "does not match the requested case"):
            load_verified_resume_items(self.manifest, [self.case], self.output, True)

    def test_atomic_manifest_is_valid_json(self) -> None:
        self.assertEqual(json.loads(self.manifest.read_text()), [self.item])


if __name__ == "__main__":
    unittest.main()
