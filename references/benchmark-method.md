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

Release reporting must show results by band and genre, not only one aggregate percentage. Failed variants must be evaluated from the materialized image, not from the original URL preview.

## Leakage and validity checks

The validator fails on duplicate IDs, duplicate source pages or image URLs, overlap with teaching masterworks, unknown pattern IDs, unsupported labels, missing licence/provenance, undersized observation keys, missing recipes, band-count mismatches, or inadequate genre coverage. Human visual review remains required: schema validity cannot prove that the expected observation is correct.
