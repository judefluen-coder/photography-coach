#!/usr/bin/env python3
"""Tests for identity-safe image reuse when preparing blind runs."""

from __future__ import annotations

import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import prepare_blind_run
from prepare_blind_run import load_verified_reuse_items, reused_materialization_record


ROOT = Path(__file__).resolve().parent.parent
KNOWN_STALE_V4_MANIFEST = ROOT / ".benchmark-runs" / "v4-materialized" / "manifest.json"


class ReuseManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.reuse_dir = Path(self.temporary.name) / "reuse"
        self.reuse_dir.mkdir()
        self.image_path = self.reuse_dir / "v4-001.jpg"
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
            "blind_prompt": "Please critique this image.",
        }
        self.item = {
            "id": self.case["id"],
            "quality_band": self.case["quality_band"],
            "genre": self.case["genre"],
            "source_page": self.case["source_page"],
            "download_url": self.case["preview_url"],
            "source_sha1": self.case["source_sha1"],
            "variant_recipe": self.case["variant_recipe"],
            "output_path": str(self.image_path),
            "output_sha256": hashlib.sha256(self.image_path.read_bytes()).hexdigest(),
            "output_width": 32,
            "output_height": 24,
        }
        self.manifest_path = self.reuse_dir / "manifest.json"
        self.write_manifest(self.item)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_manifest(self, item: dict[str, object]) -> None:
        self.manifest_path.write_text(json.dumps([item]), encoding="utf-8")

    def test_legal_reuse_is_verified_and_preserves_identity(self) -> None:
        verified = load_verified_reuse_items(
            self.manifest_path, [self.case], self.reuse_dir, use_original=False
        )
        destination = Path(self.temporary.name) / "run" / "v4-001.jpg"
        destination.parent.mkdir()
        destination.write_bytes(self.image_path.read_bytes())
        record = reused_materialization_record(
            self.case, verified["v4-001"], destination
        )
        for field in (
            "source_sha1",
            "source_page",
            "variant_recipe",
            "quality_band",
            "genre",
        ):
            self.assertEqual(record[field], self.case[field])
        self.assertEqual(record["output_path"], str(destination))
        self.assertEqual(record["output_sha256"], self.item["output_sha256"])

    def test_stale_cache_identity_is_rejected(self) -> None:
        for field, stale_value in (
            ("source_sha1", "b" * 40),
            ("source_page", "https://example.test/old-source"),
            ("variant_recipe", {"operation": "shadow_crush", "parameters": {}}),
            ("quality_band", "acclaimed"),
            ("genre", "portrait"),
        ):
            with self.subTest(field=field):
                stale = dict(self.item)
                stale[field] = stale_value
                self.write_manifest(stale)
                with self.assertRaisesRegex(ValueError, rf"{field} mismatch"):
                    load_verified_reuse_items(
                        self.manifest_path,
                        [self.case],
                        self.reuse_dir,
                        use_original=False,
                    )

    def test_reuse_directory_image_manifest_mismatch_is_rejected(self) -> None:
        Image.new("RGB", (32, 24), (200, 10, 10)).save(self.image_path)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            load_verified_reuse_items(
                self.manifest_path, [self.case], self.reuse_dir, use_original=False
            )

    def test_missing_trusted_manifest_is_rejected(self) -> None:
        self.manifest_path.unlink()
        with self.assertRaisesRegex(ValueError, "trusted reuse manifest is missing"):
            load_verified_reuse_items(
                self.manifest_path, [self.case], self.reuse_dir, use_original=False
            )

    @unittest.skipUnless(
        KNOWN_STALE_V4_MANIFEST.is_file(),
        "local v4 incident artifact is not present",
    )
    def test_known_stale_v4_materialization_is_rejected(self) -> None:
        cases = prepare_blind_run.load_cases(ROOT / "references" / "benchmark-cases.jsonl")
        with self.assertRaisesRegex(ValueError, "source_sha1 mismatch"):
            load_verified_reuse_items(
                KNOWN_STALE_V4_MANIFEST,
                cases,
                KNOWN_STALE_V4_MANIFEST.parent,
                use_original=False,
            )

    def test_preview_manifest_cannot_resume_as_original(self) -> None:
        with self.assertRaisesRegex(ValueError, "download_url mismatch"):
            load_verified_reuse_items(
                self.manifest_path,
                [self.case],
                self.reuse_dir,
                use_original=True,
            )

    def test_prepared_run_keeps_rich_manifest_but_blind_input_is_clean(self) -> None:
        cases_path = Path(self.temporary.name) / "cases.jsonl"
        cases_path.write_text(json.dumps(self.case) + "\n", encoding="utf-8")
        run_root = Path(self.temporary.name) / "runs"
        argv = [
            "prepare_blind_run.py",
            "--cases",
            str(cases_path),
            "--run-id",
            "legal-reuse",
            "--reuse-images-from",
            str(self.reuse_dir),
        ]
        with patch.object(prepare_blind_run, "DEFAULT_RUN_ROOT", run_root), patch(
            "sys.argv", argv
        ):
            self.assertEqual(prepare_blind_run.main(), 0)

        run_dir = run_root / "legal-reuse"
        run_manifest = json.loads(
            (run_dir / "materialization-manifest.json").read_text(encoding="utf-8")
        )
        blind_input = json.loads(
            (run_dir / "blind-inputs.jsonl").read_text(encoding="utf-8")
        )
        for field in (
            "source_sha1",
            "source_page",
            "variant_recipe",
            "quality_band",
            "genre",
        ):
            self.assertEqual(run_manifest[0][field], self.case[field])
            self.assertNotIn(field, blind_input)

    def test_parallel_materialization_keeps_manifest_order_and_file_coverage(self) -> None:
        cases = []
        for index in range(1, 4):
            cases.append({
                **self.case,
                "id": f"v5-{index:03d}",
                "source_sha1": f"{index:040x}",
                "source_page": f"https://example.test/source/{index}",
                "image_url": f"https://example.test/original/{index}.jpg",
                "preview_url": f"https://example.test/preview/{index}.jpg",
            })
        cases_path = Path(self.temporary.name) / "parallel-cases.jsonl"
        cases_path.write_text(
            "".join(json.dumps(case) + "\n" for case in cases), encoding="utf-8"
        )
        run_root = Path(self.temporary.name) / "parallel-runs"

        def fake_materialize(case, output, use_original):
            time.sleep({"v5-001": .03, "v5-002": .02, "v5-003": .01}[case["id"]])
            destination = output / f"{case['id']}.jpg"
            Image.new("RGB", (16, 12), (10, 20, 30)).save(destination)
            return {
                "id": case["id"],
                "quality_band": case["quality_band"],
                "genre": case["genre"],
                "source_page": case["source_page"],
                "download_url": case["preview_url"],
                "source_sha1": case["source_sha1"],
                "output_path": str(destination),
                "output_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "variant_recipe": case["variant_recipe"],
            }

        argv = [
            "prepare_blind_run.py", "--cases", str(cases_path), "--run-id",
            "parallel", "--workers", "3",
        ]
        with patch.object(prepare_blind_run, "DEFAULT_RUN_ROOT", run_root), patch.object(
            prepare_blind_run, "materialize", fake_materialize
        ), patch("sys.argv", argv):
            self.assertEqual(prepare_blind_run.main(), 0)

        run_dir = run_root / "parallel"
        manifest = json.loads(
            (run_dir / "materialization-manifest.json").read_text(encoding="utf-8")
        )
        blind_ids = [
            json.loads(line)["case_id"]
            for line in (run_dir / "blind-inputs.jsonl").read_text().splitlines()
            if line.strip()
        ]
        self.assertEqual([item["id"] for item in manifest], blind_ids)
        self.assertEqual(
            {path.stem for path in (run_dir / "images").glob("*.jpg")},
            {item["id"] for item in manifest},
        )


if __name__ == "__main__":
    unittest.main()
