# Visual report contract

Use this contract when the Codex app can return a local visual artifact and the user wants a page, interface, or downloadable treatment rather than chat-only critique.

## Purpose

Render the ordinary Photography Coach critique as a reusable local HTML report. Keep the useful judgment in chat, then link the page as the durable visual surface. This is not a standalone app and does not call a model or edit pixels by itself.

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
- Each observation may include `regions`, up to four rectangles `{ "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.2 }`. Coordinates are fractions of the original image from its top-left. Identify regions by inspecting the image. Multiple rectangles can explain a distance or relationship. The page displays these only on its dedicated original-image view, never over cropped output.
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
- Optional `source_preview_image`, `color_preview_image`, and `treatment_preview_image` provide smaller display exports of their corresponding masters. A preview requires its master; do not substitute it for the full-size download. The renderer copies both into the output so the report remains portable, and creates asset/download paths itself. Do not hand-author `*_asset` or `*_download` fields.
- Compare source and color-only at identical framing and scale; show the combined version separately when present. The renderer checks paths and structure, not pixel fidelity, matching framing, edit quality, or whether the crop was actually derived from the color-only master; these require source/result inspection and, where feasible, pixel checks before rendering.
- Never show a generated approximation as a develop. If content changed, omit it and render the exact recipe instead.
- Link one exact verified reference by default. Do not embed it unless its specific license permits redistribution.
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
