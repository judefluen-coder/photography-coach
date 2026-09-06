#!/usr/bin/env python3
"""Regression tests for bilingual knowledge retrieval."""

from __future__ import annotations

import unittest

from search_knowledge import COLLECTIONS, expand_query, load_aliases, load_jsonl, score


class ChineseRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aliases = load_aliases()
        cls.patterns = load_jsonl(COLLECTIONS["patterns"])

    def top_pattern(self, query: str) -> str:
        tokens = expand_query(query, self.aliases)
        ranked = sorted(
            ((score(record, tokens), record["id"]) for record in self.patterns),
            key=lambda pair: (-pair[0], pair[1]),
        )
        self.assertGreater(ranked[0][0], 0)
        return ranked[0][1]

    def test_crop_pressure_query(self) -> None:
        self.assertEqual(
            self.top_pattern("裁切压迫"),
            "pattern-crop-pressure-compares-opposite-edges",
        )

    def test_shadow_crush_query(self) -> None:
        self.assertEqual(
            self.top_pattern("暗部压死"),
            "pattern-global-shadow-compression-needs-multiple-boundaries",
        )

    def test_color_excess_query(self) -> None:
        self.assertEqual(
            self.top_pattern("色彩过度"),
            "pattern-color-excess-preserves-material-differences",
        )

    def test_roll_query(self) -> None:
        self.assertEqual(
            self.top_pattern("画面倾斜裁切"),
            "pattern-roll-and-crop-require-independent-references",
        )


if __name__ == "__main__":
    unittest.main()
