# Clean-context blind evaluator prompt

You are evaluating Photography Coach as a response writer, not grading it. Work from the supplied blind packet only.

## Allowed inputs

- `SKILL.md`
- `references/evaluation-standard.md`
- `references/integrity-preflight.md`
- `references/response-card.md`
- `references/reference-policy.md`
- `references/knowledge-method.md`
- `references/critique-patterns.jsonl`
- `references/masterwork-cards.jsonl`
- `references/source-registry.jsonl`
- `scripts/search_knowledge.py`
- `scripts/analyze_image_integrity.py`
- `scripts/validate_response.py`
- `scripts/validate_blind_responses.py`
- the run's `blind-inputs.jsonl` and `images/`

Do not open or search any of the following until every response has been saved and frozen:

- `references/benchmark-cases.jsonl`
- `references/benchmark-method.md`
- `references/benchmark-report.json`
- every `annotation-audit.jsonl`, selection file, candidate manifest, materialization manifest, grade file, diagnostic file, or report under `.benchmark-runs/`
- `scripts/materialize_benchmark.py`
- any previous critique, contact sheet, source title, author, award, category, licence, or quality label for a benchmark image

## Task

For each line in `blind-inputs.jsonl`, inspect only its `image_path` at the highest useful resolution and write one independent Chinese audit/export-mode critique to its `response_path`.

Each response must:

1. follow all 12 headings in `references/response-card.md`;
2. inspect the image before reading the quantitative result, then record a scene-topology snapshot with repeated units/states, one start-to-end path, one exception/interruption, edge endpoints, and a scale anchor;
3. run the integrity probe, treating its signals only as inspection candidates, and complete the operation-specific crop, tilt, and detail tests;
4. begin from localized visible evidence and scan the whole frame, not only the presumed subject;
5. choose exactly one decision token and one main priority;
6. protect two existing visible relationships before proposing a structural correction, and require a concrete localized information loss for `STRUCTURAL_BOTTLENECK`;
7. include all eight 0–5 intervals with image-specific reasons and no total;
8. distinguish immediate editing from information that cannot be recovered;
9. include one bounded 20–40 minute exercise;
10. use one or two exact, verified single-work references when available, with a looking task, relevance, difference, and transferable experiment;
11. avoid identities, motives, relationships, consent, staging, location, equipment, exposure settings, or off-frame events that are not visible;
12. never read the answer key to resolve uncertainty.

Do not reuse prose across cases. Treat every photograph as independent; previous images do not establish a house style or expected quality. An unusual crop, blur, darkness, colour, symmetry, or empty area is not automatically a defect. Conversely, do not excuse a shared readability failure as style.

After each response, run `python3 scripts/validate_response.py --benchmark RESPONSE_PATH` and fix structural failures without changing the visual judgment merely to satisfy wording checks. After all cases, run `python3 scripts/validate_blind_responses.py RUN_DIR`. Stop before grading and report only the frozen response count and validation result.
