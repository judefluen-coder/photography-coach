#!/usr/bin/env python3
"""Build a deterministic exclusion index of every previously used source."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = (
    ROOT / ".benchmark-runs" / "v5-draft" / "historical-source-exclusions.json"
)
TRACKING_QUERY_NAMES = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "referrer",
    "source",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}
SHA1_RE = re.compile(r"[0-9a-f]{40}")
MANIFEST_CONTAINERS = ("items", "records", "sources", "cases", "entries")


def normalized_url(value: Any) -> str:
    """Return a stable HTTP(S) URL identity, or an empty string if invalid."""
    if not isinstance(value, str) or not value.strip():
        return ""
    parsed = urllib.parse.urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return ""
    host = parsed.hostname.casefold().removeprefix("www.")
    try:
        port = parsed.port
    except ValueError:
        return ""
    netloc = host if port in {None, 80, 443} else f"{host}:{port}"
    decoded_path = urllib.parse.unquote(parsed.path)
    if host == "commons.wikimedia.org" and decoded_path.startswith("/wiki/"):
        prefix, title = decoded_path.split("/wiki/", 1)
        decoded_path = f"{prefix}/wiki/{title.replace(' ', '_')}"
    path = urllib.parse.quote(
        decoded_path.rstrip("/") or "/",
        safe="/:@!$&'()*+,;=-._~",
    )
    query = [
        (name, item)
        for name, item in urllib.parse.parse_qsl(
            parsed.query, keep_blank_values=True
        )
        if name.casefold() not in TRACKING_QUERY_NAMES
    ]
    suffix = f"?{urllib.parse.urlencode(sorted(query))}" if query else ""
    return f"https://{netloc}{path}{suffix}"


def normalized_sha1(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    candidate = value.strip().casefold()
    return candidate if SHA1_RE.fullmatch(candidate) else ""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"{path}:{line_number}: JSONL record must be an object")
        records.append(record)
    return records


def manifest_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = next(
            (
                payload[name]
                for name in MANIFEST_CONTAINERS
                if isinstance(payload.get(name), list)
            ),
            [],
        )
    else:
        records = []
    return [record for record in records if isinstance(record, dict)]


def relative_source(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def source_identity(
    record: dict[str, Any],
    source_file: str,
    *,
    masterwork: bool = False,
) -> dict[str, Any] | None:
    pages = {
        normalized_url(record.get(field))
        for field in (
            ("direct_url", "source_url", "source_page")
            if masterwork
            else ("source_page",)
        )
    }
    pages.discard("")
    sha1 = normalized_sha1(record.get("source_sha1"))
    image_urls: set[str] = set()
    if not masterwork:
        # download_url is the image_url name used by the old materializer schema.
        for field in ("image_url", "download_url"):
            value = normalized_url(record.get(field))
            if value:
                image_urls.add(value)
    if not pages and not sha1 and not image_urls:
        return None
    return {
        "source_pages": pages,
        "source_sha1s": {sha1} if sha1 else set(),
        "image_urls": image_urls,
        "source_files": {source_file},
    }


def input_paths(root: Path) -> tuple[list[Path], list[Path], list[Path]]:
    references = root / "references"
    case_paths = sorted(references.glob("benchmark*-cases.jsonl"))
    run_root = root / ".benchmark-runs"
    manifest_paths = sorted(
        {
            *run_root.glob("**/materialization-manifest.json"),
            *run_root.glob("**/manifest.json"),
        }
    )
    masterwork_paths = sorted(references.glob("masterwork-cards.jsonl"))
    return case_paths, manifest_paths, masterwork_paths


def collect_identities(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    case_paths, manifest_paths, masterwork_paths = input_paths(root)
    identities: list[dict[str, Any]] = []
    all_paths = [*case_paths, *manifest_paths, *masterwork_paths]
    for path in case_paths:
        source_file = relative_source(path, root)
        identities.extend(
            identity
            for record in load_jsonl(path)
            if (identity := source_identity(record, source_file)) is not None
        )
    for path in manifest_paths:
        source_file = relative_source(path, root)
        identities.extend(
            identity
            for record in manifest_records(path)
            if (identity := source_identity(record, source_file)) is not None
        )
    for path in masterwork_paths:
        source_file = relative_source(path, root)
        identities.extend(
            identity
            for record in load_jsonl(path)
            if (
                identity := source_identity(record, source_file, masterwork=True)
            )
            is not None
        )
    return identities, [relative_source(path, root) for path in all_paths]


def identity_tokens(identity: dict[str, Any]) -> set[str]:
    return {
        *{f"page:{value}" for value in identity["source_pages"]},
        *{f"sha1:{value}" for value in identity["source_sha1s"]},
        *{f"image:{value}" for value in identity["image_urls"]},
    }


def merge_identities(identities: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge records transitively when any non-empty source identity matches."""
    rows = list(identities)
    parents = list(range(len(rows)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parents[max(left_root, right_root)] = min(left_root, right_root)

    token_owners: dict[str, int] = {}
    for index, identity in enumerate(rows):
        for token in identity_tokens(identity):
            owner = token_owners.setdefault(token, index)
            union(index, owner)

    groups: dict[int, dict[str, set[str]]] = defaultdict(
        lambda: {
            "source_pages": set(),
            "source_sha1s": set(),
            "image_urls": set(),
            "source_files": set(),
        }
    )
    for index, identity in enumerate(rows):
        group = groups[find(index)]
        for field in group:
            group[field].update(identity[field])

    merged = [
        {field: sorted(values) for field, values in group.items()}
        for group in groups.values()
    ]
    merged.sort(
        key=lambda item: (
            item["source_sha1s"],
            item["source_pages"],
            item["image_urls"],
            item["source_files"],
        )
    )
    return merged


def build_index(root: Path) -> dict[str, Any]:
    identities, inputs = collect_identities(root)
    sources = merge_identities(identities)
    source_pages = sorted(
        {value for source in sources for value in source["source_pages"]}
    )
    source_sha1s = sorted(
        {value for source in sources for value in source["source_sha1s"]}
    )
    image_urls = sorted(
        {value for source in sources for value in source["image_urls"]}
    )
    hashed_payload = {
        "schema_version": 1,
        "source_files": sorted(inputs),
        "source_sha1s": source_sha1s,
        "source_pages": source_pages,
        "image_urls": image_urls,
        "sources": sources,
    }
    canonical = json.dumps(
        hashed_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    snapshot_sha256 = hashlib.sha256(canonical).hexdigest()
    return {
        **hashed_payload,
        "source_count": len(sources),
        # Both names are retained: overall_sha256 is the consumer contract,
        # while snapshot_sha256 makes the value's scope explicit to humans.
        "overall_sha256": snapshot_sha256,
        "snapshot_sha256": snapshot_sha256,
    }


def write_index(index: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root to scan (primarily useful for tests)",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    index = build_index(args.root)
    write_index(index, args.output)
    print(
        f"Wrote {index['source_count']} historical source exclusions from "
        f"{len(index['source_files'])} files to {args.output} "
        f"({index['snapshot_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
