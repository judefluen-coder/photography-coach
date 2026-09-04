#!/usr/bin/env python3
"""Unit tests for deterministic blind-benchmark transformations."""

from __future__ import annotations

import unittest

from PIL import Image

from materialize_benchmark import apply_recipe, mean_absolute_difference


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


if __name__ == "__main__":
    unittest.main()
