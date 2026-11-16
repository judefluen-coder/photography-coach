# Visual report contract

Use this contract when the Codex app can return a local visual artifact and the user wants a page, interface, or downloadable treatment rather than chat-only critique.

## Purpose

Render the ordinary Photography Coach critique as a reusable local HTML darkroom workspace. Keep the useful judgment in chat, then link the page as the durable visual surface. The same template is embedded by the independent Web app; a generated report is not itself an upload/model endpoint.

## Darkroom presentation

- Use the shared charcoal/citron system by default, with an optional light theme. No custom theme or screenshot per photograph.
- One main canvas carries the photograph and click-open explanations. Default to the full frame, preserve aspect ratio, and explicitly label local enlargement. Never stretch, outpaint or silently crop a picture to fit the interface.
- The dock shows the eight interval axes, a local before/after when real files and a valid discussed region exist, and the main action or protection. Keep full observations, checks, reasons, edit limits, exact reference and exercise below; visual prioritization must not delete evaluation coverage.
- `title` and `priority.title` should give a direct conclusion, preservation decision or concrete action. Explain visible evidence, uncertainty and cost in the corresponding body. Short labels are not a substitute for the complete critique.
- Only a supplied `color_image` enables same-framing comparison and tone-strength controls. Strength is an honest blend of source and color-only pixels, not a measured exposure value or a new local-edit model. Full-resolution mixed export is a browser operation; if unavailable, retain the original master downloads and show the limitation.
- Original-coordinate marks can be shown on the source and the same-framing tonal comparison. Hide them on cropped treatment output. Re-enter the source when a user selects an observation or crop guide; never put source coordinates over a different crop.
- Do not show inactive exposure sliders, fake download states, inferred progress metrics, an overall score, or a reference thumbnail without a verified asset/license.

## Required flow

1. Finish the image inspection, integrity preflight, diagnosis, knowledge search, and source verification before building the report.
2. Produce the critique in the ordinary response-card hierarchy and map it into the JSON fields below.
3. When the user requested an edit, create and inspect a faithful non-destructive treatment first. Pass it to the renderer only if people, objects, text, gestures, and documentary content remain unchanged.
4. Write the JSON and rendered report to a task-specific output directory outside the skill repository. Do not commit user photographs or reports.
5. Run `scripts/render_visual_report.py`, open the result, and check desktop and narrow layouts before linking it.
6. Keep the chat handoff short: one-sentence judgment, report link, treatment link when present, and material limitations.

## JSON shape

All text uses the user's language. `source_image` and `treatment_image` may be absolute paths or paths relative to the JSON file. Omit `treatment_image` when there is no inspected, faithful edit.

```json
{
  "title": "画面有三层，但主次还没站稳。",
  "source_image": "/absolute/path/source.jpg",
  "color_image": "/absolute/path/color-only.png",
  "treatment_image": "/absolute/path/treatment.jpg",
  "summary": "Two or three short sentences in plain language.",
  "priority": {
    "title": "One concrete leading correction.",
    "body": "Visible evidence and likely effect."
  },
  "strength": {
    "title": "One relation to protect.",
    "body": "Two localized observations and what they preserve."
  },
  "observations": [
    {"label": "构图", "priority": "首要", "text": "Visible fact and likely effect."}
  ],
  "scores": [
    {"dimension": "技术可读性", "interval": "3-4 / 5", "reason": "Image-specific reason."}
  ],
  "reshoot": {
    "action": "Scene-ready instruction.",
    "effect": "Expected viewing effect.",
    "cost": "What the change may lose.",
    "availability": "即时"
  },
  "edit": {
    "summary": "What the delivered treatment changes.",
    "crop": "Visible crop landmarks or proportions.",
    "tone_color": "Ordered tonal and color changes.",
    "limit": "What editing cannot recover."
  },
  "reference": {
    "photographer": "Creator",
    "title": "Exact work title",
    "year": "1994",
    "url": "https://direct-single-work-page.example",
    "looking_task": "A 20-60 second looking task.",
    "match": "The relation between two localized things in this photo and the same visible mechanism in the reference.",
    "difference": "A meaningful difference that prevents copying."
  },
  "exercise": {
    "title": "One constrained practice target.",
    "instructions": "Timebox, shot count, one variable, and pass/fail criterion."
  },
  "boundary_note": "Material unknowns and fact boundary in natural language.",
  "research_status": "实验版 v1.6。不是专家认证、客观审美分或学习效果证明。"
}
```

## Validation rules

- Optional `decision` is one of `STRUCTURAL_BOTTLENECK`, `CONDITIONAL_BRANCH`, or `NO_STRUCTURAL_BOTTLENECK`; it changes the leading labels so a sound photograph is not presented as broken.
- Each observation may include `regions`, up to four rectangles `{ "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.2 }`. Coordinates are fractions of the original image from its top-left. Identify regions by inspecting the image. Multiple rectangles can explain a distance or relationship. The page uses these on the main source/same-framing tonal canvas, never over cropped output.
- Optional `visual_guides` contains zero to three image-specific teaching diagrams. Each has `title` (up to 24 characters), `takeaway` and `boundary` (up to 240 each), plus arrays `areas`, `lines`, and `labels`. The page pairs marks on the original with a simplified diagram; users can hide the marks or return to the full observations. Older reports without this field remain supported; new API output includes the field, using `[]` when a diagram would not help.
- A guide area is `{ "tone": "accent", "points": [{ "x": 0.1, "y": 0.2 }, ...] }`; use 3–24 points and at most six areas. Lines use 2–24 points, the same `tone`, and a boolean `arrow`; use at most eight lines. Labels are `{ "x": 0.5, "y": 0.1, "text": "近处的人" }`, at most six, each up to 24 characters. All coordinates are finite fractions within 0–1 of the original image. Fixed tones are `accent`, `secondary`, `dark`, `light`, `warm`, `cool`; these are explanatory colors, not sampled measurements.
- Choose what is genuinely useful: relative sizes, gaps, overlap, visible lines, tonal masses, or existing frame edges. Inspect locations and label placement against the original. Do not fabricate eye tracking, physical distances, off-frame detail, or a camera position. `boundary` must explain the simplification. A teaching diagram is not a developed photograph, segmentation result, or a simulated reshoot; it never substitutes for the requested real edit.
- A label may include `explanation` (up to 160 characters): one or two sentences about that specific mark. New API responses include it; legacy labels fall back to the guide's `takeaway`. Clicking a photo label or observation pin opens its explanation on the photo; clicking again, outside, hiding the marks, changing guides, or pressing Escape closes it. Only one explanation is open at a time. Do not repeat the same explanation below the image. Unlocalized observations retain their text fallback; never invent a location just to create a pin. A guide without labels gets an explicitly general `图解说明` control rather than losing its takeaway.
- Optional `learning_check` is one skippable comparison of two editing approaches for this photograph, not a quiz gate or aesthetic score. Use `null` or omit it when there is no useful comparison. It contains `observation_index` (zero-based integer referencing an existing observation), `question` (up to 80 characters), exactly two `options` with `title` (24), `effect` (120), `cost` (120), and `takeaway` (160). Link the question to a concrete observation and the existing edit advice; explain both approaches' effects and costs, with a visible stop condition. Do not invent a universal correct answer, display a generated score, or claim both alternatives have been rendered. New API responses include this field, using `null` when inappropriate; old reports remain supported.
- The comparison is collapsed by default under the edit advice. The whole report and any real adjusted images remain available without answering. `跳过选择，直接看解释` reveals the same complete explanation as a selection. Choices are local UI state only, not a saved learning history. A related localized observation can jump to edit advice; the comparison can return to that same observation. Do not guess links from arbitrary labels or create fake coordinates for unlocalized observations.
- Present `edit.tone_color` separately from `edit.crop`, with an explicit asset-availability label. A real `color_image` enables a jump to the same-framing slider; source-only and legacy crop-only reports must not acquire a simulated color comparison. Diagrams, A/B method descriptions, and the existence of an edit recipe are not evidence of an actual developed file.
- `edit.crop_region` uses the same coordinates and marks the retained area. It must describe the actual crop when a treatment is supplied.
- Each score may carry a plain-language `uncertainty` string. Do not invent confidence percentages.
- Optional `integrity` carries six `{ "family": "暗部", "verdict": "观察", "basis": "Localized evidence" }` records, ordered as `边缘/裁切`, `暗部`, `高光`, `色彩`, `轴线/透视`, `细节`; use only `通过`, `观察`, or `问题`. Supply it for new critiques so the six-check summary survives rendering; older reports without it remain supported.
- For third-party example images, `source_credit` carries `author`, direct `url`, `license`, `license_url`, and `changes` (including derivative-license terms and no endorsement). It is displayed as text and validated links, never raw HTML. Preserve attribution when moving an example from a custom page into the common renderer.
- The practice section copies a self-contained follow-up prompt for use with a new photograph in Codex. It is not an upload endpoint or automatic progress tracker.

- Include exactly the eight stable score dimensions from `response-card.md`; never add a total.
- Include six to nine prioritized observations. Use exactly one `首要`, two to five `次要`, and at least one `要保护`.
- Keep the first screen to the photograph, judgment, summary, priority, and treatment control.
- Optional `color_image` is an inspected full-frame color-only master, not a crop or a generated approximation. When both it and `treatment_image` are supplied, the latter is the combined treatment; `edit.crop_region` describes its actual crop. Do not force cropping where there is no useful crop.
- The renderer supports source-only, source + color-only, legacy source + treatment, and all three. Missing versions are hidden, never replaced with copies of the source. Legacy reports remain readable and explicitly say when color was not separately supplied.
- Default to color-only when supplied, otherwise treatment when supplied, otherwise source. The current-version download follows the selection. All supplied masters have their own download links.
- With a color-only asset, the optional sliding comparison shows source on the left and color on the right, at the same framing and scale. It never compares a crop against the uncropped source. Hide the current-version master download during this composite view; selecting any real version restores its full-size download. A separate mixed-tone export, when available, saves only the chosen full-frame tone strength, not a screenshot of the split view. The native range controls must work with the keyboard. Reports without a color-only asset do not offer these controls.
- Optional `source_preview_image`, `color_preview_image`, and `treatment_preview_image` provide smaller display exports of their corresponding masters. A preview requires its master; do not substitute it for the full-size download. The renderer copies both into the output so the report remains portable, and creates asset/download paths itself. Do not hand-author `*_asset` or `*_download` fields.
- Compare source and color-only at identical framing and scale; show the combined version separately when present. The renderer checks paths and structure, not pixel fidelity, matching framing, edit quality, or whether the crop was actually derived from the color-only master; these require source/result inspection and, where feasible, pixel checks before rendering.
- Never show a generated approximation as a develop. If content changed, omit it and render the exact recipe instead.
- Link one exact verified reference by default. Do not embed it unless its specific license permits redistribution.
- If no reliable exact work has been verified, set `reference` to `null` and supply a non-empty `reference_status` explaining the gap. The page must show that status and hide the reference link, never fill the slot with an unrelated or invented work. Omitting `reference` entirely remains invalid.
- Treat the bundled reference library as a starting set, not a ceiling. Use an externally verified exact work when no bundled card clears the reference fit gate.
- The reference match must localize the shared mechanism in both photographs. Shared subject matter, genre, palette, mood, or fame alone is not a match.
- Prefer everyday descriptions such as `左边的虚影` before terms such as `前景遮挡`.
- Keep the page in one neutral dark theme so surrounding color does not compete with the photograph.

## Renderer

```bash
python3 scripts/render_visual_report.py \
  --input /absolute/path/report.json \
  --output /absolute/path/rendered-report
```

The renderer fails on missing fields, unsafe reference URLs, wrong score dimensions, invalid priority counts, missing image files, or a non-empty output directory. Pass `--force` only when replacing a known task-specific report directory.
