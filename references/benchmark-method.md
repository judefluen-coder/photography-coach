# Blind benchmark method

This benchmark tests whether the coach can observe, prioritize, and bound its claims. It is not a popularity contest and does not claim that community recognition is objective truth.

## Independent holdout

- Every case uses an exact Wikimedia Commons file page and an open licence or public-domain mark.
- No benchmark source page may appear in `masterwork-cards.jsonl`.
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

1. Create the packet with `python3 scripts/prepare_blind_run.py --run-id NAME`. Interrupted downloads may be continued with the same arguments plus `--resume`. The run metadata freezes a `coaching_protocol_sha256` over the skill, evaluation standard, integrity preflight, response card, and critique rules so the eventual score can be tied to the exact coaching protocol rather than only a mutable branch name.
2. Give only `blind-inputs.jsonl`, its `images/` directory, and the response contract to a clean-context evaluator. The evaluator must not open this method, the benchmark JSONL, the materialization code, or any prior critique of the images.
3. Save one frozen response at each declared `response_path`. Do not alter a response after grading begins.
4. Run `python3 scripts/report_benchmark.py RUN_DIR --init`. This refuses to make a grade sheet until every response exists and records every response SHA-256.
5. A reviewer opens the answer key, records matched zero-based `must_notice` indexes and the rubric fields, then runs `python3 scripts/report_benchmark.py RUN_DIR`.
6. Commit a report to `references/benchmark-report.json` only when its case hash matches the current corpus. For new runs, preserve the packet's `coaching_protocol_sha256` in the report. Publish failed case IDs and band/genre metrics even when the run misses release thresholds.

A separate model context is acceptable as a repeatable internal reviewer when a human photography panel is unavailable, but it is not independent expert validation. Record the exact model/version and prompt policy in `reviewer_id` and keep that limitation in the release claim.

## Leakage and validity checks

The validator fails on duplicate IDs, duplicate source pages or image URLs, overlap with teaching masterworks, unknown pattern IDs, unsupported labels, missing licence/provenance, undersized observation keys, missing recipes, band-count mismatches, or inadequate genre coverage. Human visual review remains required: schema validity cannot prove that the expected observation is correct.
