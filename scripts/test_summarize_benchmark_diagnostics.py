#!/usr/bin/env python3
"""Tests for benchmark diagnostic summarization."""

from __future__ import annotations

import unittest

from summarize_benchmark_diagnostics import summarize


class BenchmarkDiagnosticTests(unittest.TestCase):
    def test_counts_failed_checks_and_operations(self) -> None:
        cases = [
            {
                "id": "case-1",
                "quality_band": "failed_imitation",
                "genre": "landscape/nature",
                "must_notice": ["a", "b"],
                "variant_recipe": {"operation": "shadow_crush"},
            }
        ]
        grades = [
            {
                "case_id": "case-1",
                "observation_hits": [0],
                "priority_hit": False,
                "pattern_fit": 1,
                "hallucination_violation": False,
                "action_quality": 1,
                "reference_hygiene": 1,
                "score_integrity": 1,
                "overcorrection": None,
                "degradation_detected": True,
                "notes": "priority miss",
            }
        ]
        report = {
            "run_id": "run",
            "benchmark_cases_sha256": "hash",
            "passed": False,
            "metrics": {},
        }
        result = summarize(cases, grades, report)
        self.assertEqual(result["failure_reason_counts"], {"priority": 1})
        self.assertEqual(result["operation_results"]["shadow_crush"]["detected"], 1)


if __name__ == "__main__":
    unittest.main()
