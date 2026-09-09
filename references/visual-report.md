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

- Include exactly the eight stable score dimensions from `response-card.md`; never add a total.
- Include six to nine prioritized observations. Use exactly one `首要`, two to five `次要`, and at least one `要保护`.
- Keep the first screen to the photograph, judgment, summary, priority, and treatment control.
- Default to the treatment view only when `treatment_image` exists and passed source comparison.
- Show source and treatment side by side later in the report and make both downloadable.
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
