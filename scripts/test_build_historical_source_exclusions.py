#!/usr/bin/env python3
"""Tests for deterministic historical-source exclusion generation."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_historical_source_exclusions import build_index, normalized_url


class HistoricalSourceExclusionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "references").mkdir()
        (self.root / ".benchmark-runs" / "old").mkdir(parents=True)
        (self.root / ".benchmark-runs" / "new").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_json(self, relative: str, payload: object) -> None:
        (self.root / relative).write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def write_jsonl(self, relative: str, records: list[dict]) -> None:
        (self.root / relative).write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )

    def test_old_and_new_manifest_schemas_merge_with_case_identity(self) -> None:
        sha1 = "A" * 40
        page = "http://www.commons.wikimedia.org/wiki/File:Old%20Source.jpg/"
        image = "https://upload.wikimedia.org/old.jpg?utm_source=test"
        self.write_jsonl(
            "references/benchmark-v2-cases.jsonl",
            [{"source_sha1": sha1, "source_page": page, "image_url": image}],
        )
        self.write_json(
            ".benchmark-runs/old/manifest.json",
            [{
                "source_sha1": sha1.lower(),
                "source_page": "https://commons.wikimedia.org/wiki/File:Old_Source.jpg",
                "download_url": "http://upload.wikimedia.org/old.jpg",
            }],
        )
        self.write_json(
            ".benchmark-runs/new/materialization-manifest.json",
            {"schema_version": 2, "items": [{
                "source_sha1": sha1.lower(),
                "source_page": "https://commons.wikimedia.org/wiki/File:Old_Source.jpg",
                "image_url": "https://upload.wikimedia.org/old.jpg?fbclid=nope",
            }]},
        )

        index = build_index(self.root)

        self.assertEqual(index["source_count"], 1)
        self.assertEqual(index["sources"][0]["source_sha1s"], [sha1.lower()])
        self.assertEqual(
            index["sources"][0]["source_pages"],
            ["https://commons.wikimedia.org/wiki/File:Old_Source.jpg"],
        )
        self.assertEqual(
            index["sources"][0]["image_urls"],
            ["https://upload.wikimedia.org/old.jpg"],
        )
        self.assertEqual(len(index["sources"][0]["source_files"]), 3)

    def test_compact_manifest_without_source_identity_is_ignored(self) -> None:
        self.write_json(
            ".benchmark-runs/old/materialization-manifest.json",
            [{"id": "v4-001", "output_sha256": "b" * 64}],
        )

        index = build_index(self.root)

        self.assertEqual(index["source_count"], 0)
        self.assertEqual(index["sources"], [])
        self.assertIn(
            ".benchmark-runs/old/materialization-manifest.json",
            index["source_files"],
        )

    def test_masterwork_direct_and_source_urls_are_excluded(self) -> None:
        self.write_jsonl(
            "references/masterwork-cards.jsonl",
            [{
                "direct_url": "https://www.example.org/work/?utm_campaign=x&id=7",
                "source_url": "http://archive.example.org/source#details",
            }],
        )

        index = build_index(self.root)

        self.assertEqual(index["source_count"], 1)
        self.assertEqual(
            index["sources"][0]["source_pages"],
            [
                "https://archive.example.org/source",
                "https://example.org/work?id=7",
            ],
        )

    def test_invalid_sha_and_non_http_values_do_not_create_identity(self) -> None:
        self.write_jsonl(
            "references/benchmark-cases.jsonl",
            [{"source_sha1": "unknown", "source_page": "", "image_url": None}],
        )

        self.assertEqual(build_index(self.root)["sources"], [])

    def test_output_and_overall_hash_are_deterministic(self) -> None:
        rows = [
            {
                "source_sha1": "2" * 40,
                "source_page": "https://example.org/two",
            },
            {
                "source_sha1": "1" * 40,
                "source_page": "https://example.org/one",
            },
        ]
        self.write_jsonl("references/benchmark-cases.jsonl", rows)
        first = build_index(self.root)
        self.write_jsonl("references/benchmark-cases.jsonl", list(reversed(rows)))
        second = build_index(self.root)

        self.assertEqual(first, second)
        hashed_payload = {
            key: first[key]
            for key in (
                "schema_version",
                "source_files",
                "source_sha1s",
                "source_pages",
                "image_urls",
                "sources",
            )
        }
        expected = hashlib.sha256(
            json.dumps(
                hashed_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(first["overall_sha256"], expected)
        self.assertEqual(first["snapshot_sha256"], expected)


class URLNormalizationTests(unittest.TestCase):
    def test_keeps_content_query_and_sorts_it(self) -> None:
        self.assertEqual(
            normalized_url("http://www.example.org/work/?b=2&utm_source=x&a=1"),
            "https://example.org/work?a=1&b=2",
        )

    def test_rejects_non_http_urls(self) -> None:
        self.assertEqual(normalized_url("file:///tmp/image.jpg"), "")


if __name__ == "__main__":
    unittest.main()
