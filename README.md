# Photography Coach

Photography Coach is an evidence-based critique skill for a user-supplied photograph. It is designed to answer a practical question: **what is already working in this frame, what most limits it, and what should I do differently next time?**

The project is a research prototype. It does not provide an objective taste score, expert certification, authorship authentication, or proven learning improvement.

## What the user receives

Upload one photograph and ask for a critique. The coach returns:

- a decisive first reading and one protected strength;
- a whole-frame review covering edges, tone, colour, spatial relations, moment, surroundings, and meaning where relevant;
- eight visible score intervals, each with image-specific evidence and no aggregate ranking;
- exactly one leading diagnosis, purpose branch, or explicit no-rebuild decision;
- one scene-ready reshoot action, its expected effect, tradeoff, and availability;
- crop and colour instructions, plus a faithful before/after preview when requested and technically available;
- one constrained 20–40 minute exercise;
- one or two exact, verified reference photographs with a short looking task and a direct source page.

A title, EXIF record, capture story, or “why I pressed the shutter” sentence is optional. When context is absent, the coach evaluates visible relationships and keeps identity, intent, event, place, and causality explicitly uncertain.

## How to use it in Codex

1. Place this repository in the Codex skills directory as `photography-coach`.
2. Start a Codex task and attach one viewable photograph.
3. Ask, for example: `用 photography-coach 点评这张照片，并告诉我下一次怎么拍。`
4. To request a visible treatment, add: `请给裁切与调色示意，并保留人物、物体、文字和动作。`

The default response is conversational. Formal audit rails remain internal unless a benchmark, export, or detailed report is requested.

## What is under the hood

- [`SKILL.md`](SKILL.md): routing, workflow, safety boundaries, and user-facing behaviour.
- [`references/evaluation-standard.md`](references/evaluation-standard.md): the adaptive observation model and decision rules.
- [`references/integrity-preflight.md`](references/integrity-preflight.md): topology-first visual inspection and six-family technical challenge.
- [`references/response-card.md`](references/response-card.md): conversational and audit response contracts.
- [`references/source-registry.jsonl`](references/source-registry.jsonl): verified source registry.
- [`references/masterwork-cards.jsonl`](references/masterwork-cards.jsonl): exact single-photograph teaching references.
- [`references/critique-patterns.jsonl`](references/critique-patterns.jsonl): falsifiable critique rules, counterexamples, and exercises.
- [`scripts/search_knowledge.py`](scripts/search_knowledge.py): bilingual retrieval over the teaching corpus.
- [`scripts/analyze_image_integrity.py`](scripts/analyze_image_integrity.py): a quantitative attention probe; it nominates checks but never decides quality or priority.
- [`references/benchmark-method.md`](references/benchmark-method.md): source-disjoint blind-test protocol and release gates.

## Current evidence, September 8, 2026

The tracked corpus currently contains:

- 103 sources, 93 individually verified;
- 150 exact single-image reference cards;
- 55 admitted critique patterns;
- 100 active source-disjoint benchmark cases across six genres and three quality roles.

The source, genre, language, region, historical/contemporary, and methodological coverage floors are met. The last independent holdout, v3, did **not** pass the release gate. A development-only v1.5 replay reduced unsupported factual assertions but regressed scene observation and degraded-image detection. The current v1.6 protocol therefore uses a scene-topology snapshot before quantitative cues, operation-specific crop/tilt/detail tests, and a two-relation protection gate.

The new 100-image v4 holdout has been selected, materialized, visually audited, and frozen. Its blind responses and answer-aware grading are still pending. Until v4 passes unchanged thresholds, the project remains an experimental prototype rather than a validated release.

## Verification

Run the complete structural suite:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_knowledge.py
```

The release gate is intentionally stricter:

```bash
python3 scripts/validate_knowledge.py --release
```

It must fail while the current source-disjoint holdout has no complete passing report. A green structural check is not a substitute for blind evaluation.

## Repository policy

Benchmark images and working packets are local, ignored artifacts. The repository tracks source identity, licence metadata, transformations, answer-key hashes, frozen responses, grades, and reports rather than redistributing the full image corpus. Exact reference pages are used for provenance; fame or platform ranking is never scoring evidence.
