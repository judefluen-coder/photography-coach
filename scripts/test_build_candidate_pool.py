#!/usr/bin/env python3
"""Tests for source-disjoint candidate-pool freezing."""

from __future__ import annotations

import unittest

from build_candidate_pool import REQUIRED_LANES, freeze_pool


def row(index: int, genre: str, assessment: str) -> dict[str, str]:
    return {
        "candidate_id": f"candidate-{index}",
        "source_sha1": f"{index:040x}",
        "source_page": f"https://example.org/page/{index}",
        "image_url": f"https://example.org/image/{index}.jpg",
        "review_genre": genre,
        "assessment": assessment,
    }


class CandidatePoolTests(unittest.TestCase):
    def complete_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        index = 1
        for genre, quotas in REQUIRED_LANES.items():
            for assessment, count in quotas.items():
                for _ in range(count):
                    rows.append(row(index, genre, assessment))
                    index += 1
        return rows

    def test_excludes_by_each_identity_and_keeps_lane_minimums(self) -> None:
        rows = self.complete_rows()
        extras = [
            row(1001, "architecture", "ordinary"),
            row(1002, "architecture", "ordinary"),
            row(1003, "architecture", "ordinary"),
        ]
        snapshot = {
            "source_sha1s": [extras[0]["source_sha1"]],
            "source_pages": [extras[1]["source_page"]],
            "image_urls": [extras[2]["image_url"]],
        }

        kept = freeze_pool([*rows, *extras], snapshot)

        self.assertEqual(kept, rows)

    def test_fails_when_a_required_lane_is_short(self) -> None:
        rows = self.complete_rows()
        removed = rows.pop(0)
        with self.assertRaisesRegex(ValueError, "architecture/acclaimed"):
            freeze_pool(rows, {"source_sha1s": [], "source_pages": [], "image_urls": []})
        self.assertEqual(removed["review_genre"], "architecture")

    def test_rejects_duplicate_identity(self) -> None:
        rows = self.complete_rows()
        duplicate = dict(rows[-1], candidate_id="another-id")
        with self.assertRaisesRegex(ValueError, "duplicate source identity"):
            freeze_pool([*rows, duplicate], {})


if __name__ == "__main__":
    unittest.main()
