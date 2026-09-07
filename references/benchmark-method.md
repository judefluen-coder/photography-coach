# Blind benchmark method

This benchmark tests whether the coach can observe, prioritize, and bound its claims. It is not a popularity contest and does not claim that community recognition is objective truth.

## Independent holdout

- The active answer key is the source-disjoint 100-case `blind_holdout_v2`; the earlier 100 cases are retained in `benchmark-development-cases.jsonl` because their failures informed v1.2.
- Every case uses an exact Wikimedia Commons file page and an open licence or public-domain mark.
- No benchmark source page may appear in `masterwork-cards.jsonl`.
- No active holdout source page, image URL, or source SHA-1 may appear in the archived development benchmark.
- The blind prompt contains only the image and the requested critique format. Author, title, community assessment, quality band, and expected observations stay hidden until scoring.
- One source photograph may appear only once. Failed-imitation cases use their own source photographs and never reuse acclaimed or ordinary cases.
- Image files are materialized locally for evaluation and remain untracked. The repository stores URLs, attribution, licence metadata, transformations, and checks—not a duplicate image archive.

## Three bands

| Band | Count | Selection role | What it can establish |
|---|---:|---|---|
| `acclaimed` | 25 | Commons Featured Pictures: community-selected high-quality works | Whether the coach can protect intentional strengths and avoid inventing defects |
| `ordinary` | 50 | Commons Quality Images: technically competent photographs that need not be extraordinary | Whether the coach can distinguish a sound frame from a structurally memorable one |
| `failed_imitation` | 25 | Deterministic degraded variants made from separate open-licence Quality Images | Whether the coach detects a known visible failure without access to the label or recipe |

The bands are operational sampling labels, not universal aesthetic ranks. Commons' own distinction is useful here: Quality Images meet technical standards but need not be extraordinary, while Featured Pictures are selected as among the site's best. A community assessment is provenance for sampling, not the answer key for critique.

## Case record

Each JSONL record includes:

- exact source identity, creator string as supplied by the file page, licence, source page, image URL, and source SHA-1;
- one controlled genre, band, difficulty, blind split, and a short selection rationale;
- one to three expected critique-pattern IDs;
- at least two localized `must_notice` observations and at least one prohibited inference;
- `variant_recipe: null` for untouched photographs;
- a declared operation and numeric parameters for a derived failure.

Expected observations are not canned final prose. They are a compact scoring key: a response may use different wording if it localizes the same visible relation and assigns comparable priority.

The key is valid only after it has been checked against the materialized image, including any deterministic variant. Source titles, descriptions, and thumbnails are discovery aids, not annotation evidence. Before a run can be graded, every `must_notice` item must be affirmed against the exact materialized bytes, at least two visible anchors must be named, and the audit must freeze both the image SHA-256 and the `must_notice` hash. If an object label, location, or relationship is wrong, correct the key and rematerialize before blind responses begin; do not excuse the mismatch during scoring.

## Derived-failure operations

Only deterministic whole-image or crop operations are allowed. Nothing is generated, removed, reconstructed, or moved.

1. `crop_pressure`: remove a declared percentage from named edges, then resize to the source dimensions.
2. `shadow_crush`: remap luminance below a declared threshold and preserve the original colour channels proportionally.
3. `highlight_clip`: increase exposure by a declared number of stops and clip the upper range.
4. `color_excess`: apply declared saturation and white-balance multipliers.
5. `tilt_and_crop`: rotate by a declared angle, crop to remove empty corners, and resize.
6. `detail_damage`: downsample by a declared factor, resize, then apply declared blur, sharpening, or JPEG quality.

Every recipe must produce a visible but plausible learner error. Materialization rejects no-op variants and records output dimensions and SHA-256 in a local manifest.

## Scoring protocol

Score each response after revealing the key:

- **Observation recall:** proportion of `must_notice` relations correctly found and localized.
- **Priority accuracy:** whether the most consequential expected relation appears as `首要`, or is explicitly protected when it is a strength.
- **Pattern fit:** whether the advice follows at least one expected pattern without mechanically quoting it.
- **Hallucination safety:** no item from `must_not_infer` is asserted as fact.
- **Action quality:** advice is feasible, predicts an effect, names a tradeoff, and does not promise recovery of absent information.
- **Reference hygiene:** any work reference is a precise single-work link and its relevance is explained.
- **Preview fidelity:** when requested, only declared crop/tone/colour edits occur and the output is visibly different without object or person changes.

### Grade-field anchors

The grader records only unambiguous evidence; borderline matches go in `notes` and do not count as hits.

| Field | Anchor |
|---|---|
| `observation_hits` | Zero-based indexes into `must_notice`. Count a hit only when the response names the same visible object or relation and localizes it; shared vocabulary alone is not a hit. |
| `priority_hit` | `true` when the highest-value expected relation is the main diagnosis, an explicit protected strength, or the decisive branch. A buried checklist mention is `false`. |
| `pattern_fit` | `0`: absent/contradictory; `1`: mechanism is broadly right but incomplete; `2`: mechanism, action, predicted effect, and cost align. |
| `hallucination_violation` | `true` when any `must_not_infer` item is asserted as fact. A clearly marked question, alternative, or uncertainty is not a violation. |
| `action_quality` | `0`: generic, impossible, unsafe, or promises recovery of missing data; `1`: executable action with a plausible effect; `2`: also names tradeoff, availability, and a bounded fallback exercise where needed. |
| `reference_hygiene` | `0`: fabricated, dead, broad portfolio/search link, or fame used as proof; `1`: precise accessible work and relevant relation; `2`: also gives a short looking task, meaningful difference, and transferable experiment. |
| `score_integrity` | `0`: missing dimensions, false total/rank, or ethics scored aesthetically; `1`: eight intervals are present but some reasons are generic; `2`: every applicable interval has an image-specific reason and no total/percentile. |
| `overcorrection` | Acclaimed only. `true` when the response invents a structural rebuild that would damage an answer-key strength. A costed optional experiment is not overcorrection. |
| `degradation_detected` | Failed-imitation only. `true` when the response identifies the introduced failure family and localizes its visible effect. Merely saying “the edit feels off” is insufficient. |

A case passes only with at least half of its localized observations, correct priority, pattern fit ≥1, no prohibited inference, action/reference/score integrity ≥1, no acclaimed overcorrection, and detection of the known degradation where applicable. Aggregate release thresholds are declared before the run in `knowledge-status.json`; do not tune them after seeing results.

Release reporting must show results by band and genre, not only one aggregate percentage. Failed variants must be evaluated from the materialized image, not from the original URL preview.

## Run sequence

1. Create the packet with `python3 scripts/prepare_blind_run.py --run-id NAME`. Interrupted downloads may be continued with the same arguments plus `--resume`. The run metadata freezes a `coaching_protocol_sha256` over the coaching instructions, response contract, critique rules, searchable sources/masterworks, bilingual aliases, and retrieval code so the eventual score can be tied to the exact coaching protocol and knowledge snapshot rather than only a mutable branch name.
2. Before any blind response is written, run `python3 scripts/benchmark_annotation_audit.py RUN_DIR --init`. In a separate answer-aware review context, inspect every materialized image at useful resolution, fill `reviewer_id`, set `image_key_alignment` only when the objects/locations/relations match, mark each `observation_support` item, and name at least two `visible_anchors_checked`. Run the command again without `--init`; it must pass. If it fails, correct the answer key, discard the run, rematerialize, and repeat. This review checks data validity, not coach performance.
3. Give only `blind-inputs.jsonl`, its `images/` directory, the current coaching protocol, and the teaching knowledge assets to a clean-context evaluator. Do not expose `annotation-audit.jsonl`. The evaluator must not open this method, the benchmark JSONL, the materialization code, or any prior critique of the images. It must run `scripts/analyze_image_integrity.py` on each local image and may search the teaching masterwork cards for an unrelated exact-work method reference.
4. Save one frozen response at each declared `response_path`. Run `python3 scripts/validate_response.py --benchmark RESPONSE.md` per response or `python3 scripts/validate_blind_responses.py RUN_DIR` for the packet. Benchmark responses must record a completed integrity probe and include at least one compliant exact-work reference; the no-reference omission is not accepted when bundled verified cards are available. Do not alter a response after grading begins.
5. Run `python3 scripts/report_benchmark.py RUN_DIR --init`. This rechecks the benchmark response contract and the image-to-key audit, refuses to make a grade sheet until both pass, and records every response SHA-256.
6. A reviewer opens the answer key, records matched zero-based `must_notice` indexes and the rubric fields, then runs `python3 scripts/report_benchmark.py RUN_DIR`.
7. Commit a report to `references/benchmark-report.json` only when its case hash matches the current corpus. For new runs, preserve the packet's `coaching_protocol_sha256` and `annotation_audit_passed` evidence in the report. Publish failed case IDs and band/genre metrics even when the run misses release thresholds.

A separate model context is acceptable as a repeatable internal reviewer when a human photography panel is unavailable, but it is not independent expert validation. Record the exact model/version and prompt policy in `reviewer_id` and keep that limitation in the release claim.

Once answer keys, failed IDs, operation families, or response-specific errors from a holdout influence prompts, thresholds, retrieval, or code, that set becomes a development benchmark for the revised protocol. A rerun can measure regression on known failures but cannot restore independence. Release validation for the revision requires newly sourced photographs and frozen keys that were not used to design it.

## Leakage and validity checks

The validator fails on duplicate IDs, duplicate source pages or image URLs, overlap with teaching masterworks, unknown pattern IDs, unsupported labels, missing licence/provenance, undersized observation keys, missing recipes, band-count mismatches, or inadequate genre coverage. Release validation also rejects a missing or stale coaching-protocol fingerprint or a missing image-to-answer-key audit, so a passing score from an older protocol cannot certify the current skill. The audit records review evidence but does not turn a model reviewer into an independent expert panel; keep that limitation in the release claim.
