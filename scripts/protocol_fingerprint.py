#!/usr/bin/env python3
"""Compute a deterministic fingerprint for the critique protocol under test."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_RELATIVE_PATHS = (
    Path("SKILL.md"),
    Path("references/evaluation-standard.md"),
    Path("references/integrity-preflight.md"),
    Path("references/response-card.md"),
    Path("references/blind-evaluator-prompt.md"),
    Path("references/benchmark-method.md"),
    Path("references/reference-policy.md"),
    Path("references/knowledge-method.md"),
    Path("references/critique-patterns.jsonl"),
    Path("references/masterwork-cards.jsonl"),
    Path("references/source-registry.jsonl"),
    Path("references/search-aliases.json"),
    Path("scripts/search_knowledge.py"),
    Path("scripts/analyze_image_integrity.py"),
    Path("scripts/validate_response.py"),
    Path("scripts/validate_blind_responses.py"),
    Path("scripts/benchmark_annotation_audit.py"),
)


def protocol_sha256(root: Path = ROOT) -> str:
    digest = hashlib.sha256()
    for relative_path in PROTOCOL_RELATIVE_PATHS:
        path = root / relative_path
        digest.update(str(relative_path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
