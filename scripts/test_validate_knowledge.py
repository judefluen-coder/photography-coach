#!/usr/bin/env python3
"""Regression tests for knowledge validation helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validate_knowledge import (
    canonical_url,
    validate_benchmark_report,
    validate_search_aliases,
)


class CanonicalURLTests(unittest.TestCase):
    def test_content_query_parameters_remain_distinct(self) -> None:
        first = canonical_url("https://www.youtube.com/watch?v=I1oPZO91mtw")
        second = canonical_url("https://www.youtube.com/watch?v=Qw9ZQw9ZQw9")

        self.assertNotEqual(first, second)

    def test_tracking_parameters_do_not_defeat_duplicate_detection(self) -> None:
        clean = canonical_url("https://www.example.com/work?id=42")
        tracked = canonical_url(
            "https://example.com/work/?utm_source=newsletter&id=42&fbclid=abc"
        )

        self.assertEqual(clean, tracked)

    def test_query_order_does_not_change_identity(self) -> None:
        first = canonical_url("https://example.com/search?year=2025&id=42")
        second = canonical_url("https://www.example.com/search?id=42&year=2025")

        self.assertEqual(first, second)


class SearchAliasValidationTests(unittest.TestCase):
    def test_duplicate_expansion_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aliases.json"
            path.write_text(
                json.dumps({"version": 1, "aliases": {"暗部": ["shadow", "shadow"]}}),
                encoding="utf-8",
            )
            errors: list[str] = []
            validate_search_aliases(path, errors)
        self.assertIn("search alias '暗部': duplicate expansions", errors)


class BenchmarkReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.thresholds = {
            "minimum_overall_pass_rate": .8,
            "minimum_band_pass_rate": .72,
            "minimum_genre_pass_rate": .7,
            "minimum_observation_recall": .75,
            "minimum_failed_variant_detection_rate": .84,
            "maximum_acclaimed_overcorrection_rate": .16,
            "maximum_hallucination_violation_rate": .05,
        }
        self.status = {
            "release_thresholds": {"blind_cases_evaluated": 100},
            "coverage_floors": {"benchmark_acceptance": self.thresholds},
        }
        self.report = {
            "thresholds": self.thresholds,
            "blind_integrity": {
                "labels_in_blind_packet": False,
                "answers_in_blind_packet": False,
                "response_freeze_enforced": True,
            },
            "metrics": {
                "evaluated_cases": 100,
                "overall_pass_rate": .9,
                "observation_recall": .8,
                "failed_variant_detection_rate": .88,
                "acclaimed_overcorrection_rate": .08,
                "hallucination_violation_rate": .02,
                "band_pass_rates": {
                    "acclaimed": .88,
                    "ordinary": .9,
                    "failed_imitation": .92,
                },
                "genre_pass_rates": {
                    "people/documentary": .9,
                    "landscape/nature": .9,
                    "architecture/cityscape": .9,
                    "still-life/food/macro": .9,
                    "wildlife/action": .9,
                    "abstract/concept": .9,
                },
            },
            "checks": {
                "all_cases_evaluated": True,
                "overall_pass_rate": True,
                "every_band_pass_rate": True,
                "every_genre_pass_rate": True,
                "observation_recall": True,
                "failed_variant_detection_rate": True,
                "acclaimed_overcorrection_rate": True,
                "hallucination_violation_rate": True,
            },
            "passed": True,
        }

    def test_valid_report_recomputes_cleanly(self) -> None:
        errors: list[str] = []
        validate_benchmark_report(self.report, self.status, errors)
        self.assertEqual(errors, [])

    def test_forged_pass_flag_is_rejected(self) -> None:
        self.report["metrics"]["overall_pass_rate"] = .2
        errors: list[str] = []
        validate_benchmark_report(self.report, self.status, errors)
        self.assertIn(
            "benchmark report acceptance checks do not recompute from its metrics",
            errors,
        )
        self.assertIn(
            "benchmark report passed flag does not match recomputed checks",
            errors,
        )

    def test_protocol_mismatch_is_rejected(self) -> None:
        self.report["coaching_protocol_sha256"] = "a" * 64
        errors: list[str] = []
        validate_benchmark_report(
            self.report,
            self.status,
            errors,
            current_protocol_sha256="b" * 64,
        )
        self.assertIn(
            "benchmark report does not match the current coaching protocol",
            errors,
        )

    def test_release_requires_protocol_fingerprint(self) -> None:
        errors: list[str] = []
        validate_benchmark_report(
            self.report,
            self.status,
            errors,
            current_protocol_sha256="b" * 64,
            require_protocol_fingerprint=True,
        )
        self.assertIn("release requires a coaching protocol fingerprint", errors)


if __name__ == "__main__":
    unittest.main()
