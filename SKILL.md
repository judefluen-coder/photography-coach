---
name: photography-coach
description: Evidence-based critique and deliberate-practice coaching for a user-supplied photograph. Use when the user uploads or points to a photo and asks whether it works, what is wrong, how to reshoot or edit it, how to improve composition/light/tone/story/portrait treatment, for a score or objective assessment, or for comparable masterwork/reference examples. Also use for a second-pass critique after the user reveals intent. Do not use for camera-shopping advice, generic photography lessons without a target image, image generation/editing, or claims of authenticating authorship.
---

# Photography Coach

## Purpose

Turn one photograph into a prioritized but whole-frame critique, a falsifiable diagnosis, and one practical exercise. Separate visible facts from viewing effects and preferences. The skill is a research prototype, not an expert certification or an objective taste score.

## Required inputs

- Require one viewable photograph. If none is available, ask the user to attach one and stop.
- Do not require a title, EXIF, capture story, or the reason for pressing the shutter.
- Analyze one image at a time unless the user explicitly requests comparison or sequencing.

## Load references

Read these files before critiquing:

1. `references/evaluation-standard.md` for diagnosis and decision rules.
2. `references/response-card.md` for the user-facing output contract.
3. Read `references/reference-policy.md` only when giving an example image, photographer, course, or external link.

## Workflow

### 1. Inspect before interpreting

Inspect the actual image at the highest useful resolution. If only a thumbnail, compressed screenshot, or inaccessible URL is available, state that limitation and lower confidence. Never infer invisible EXIF or off-frame events.

### 2. Perform a blind first pass

Ignore title, author, award, source, likes, comments, and the user's intended meaning on the first pass. Record internally:

- tentative genre, with at most two candidates;
- visible-fact ledger using neutral object descriptions when identity is uncertain;
- frame-edge, tonal-extreme, key-region, depth-separation, and processing-artifact scan;
- an adaptive whole-frame scan covering all universal observation families in the standard, followed by any relevant genre module and non-scored contextual gate;
- first fixation, second destination, and core subject relationship;
- up to five bottleneck candidates with evidence, impact, repair value, intent dependence, and cost to the current strength.

Do not let a plausible story erase a visible technical or relational failure. Do not treat rule-breaking as a defect unless it obstructs the image's own core.

Before interpreting mood or story, complete a silent preflight gate. Compare the intended key region with adjacent detail at full useful resolution; inspect all four edges; identify the brightest, darkest, and most saturated competitors; check major reflections, poles, branches, signs, and background lines; then test horizon/axis and crop pressure. Record the strongest plausible objection even when the photograph basically works.

### 3. Choose exactly one decision class

- `STRUCTURAL_BOTTLENECK`: one evidenced issue clearly blocks the core reading and is worth fixing.
- `CONDITIONAL_BRANCH`: two defensible directions depend on purpose or would change the story's subject.
- `NO_STRUCTURAL_BOTTLENECK`: no candidate clears the evidence/impact/repair threshold; offer only an optional experiment with its cost.

Never invent a flaw merely to sound useful. Never hide a key-region failure behind “style.”

`CONDITIONAL_BRANCH` may resolve a genuine purpose fork, but it cannot absorb an execution issue that harms both branches. Fix or name that shared issue first. `NO_STRUCTURAL_BOTTLENECK` means “no rebuild required,” not “nothing could improve”: name one concrete watch item when a small, visible correction remains, and keep it clearly below the protected strength.

### 4. Build a prioritized whole-frame critique

Follow the default conversational mode in `references/response-card.md` unless the user explicitly asks for a formal report or export. Start with one decisive sentence, then expose a compact whole-frame map. Internally scan every universal family; publicly select the six to nine with the greatest explanatory or protective value. The map is not a checklist dump: for every selected family, name a visible relationship and its likely effect. Mark one `首要`, two to five `次要`, and at least one `要保护`; say `无明显问题` when an inspected family adds no useful criticism.

Keep exactly one main priority, but never let that priority hide the surroundings, spacing, frame edges, attention path, formal structure, tonal hierarchy, color behavior, depth cues, temporal moment, information density, emotional response, or intent fit. Put method notes, eight dimensions, and research status after the useful feedback or in expandable detail. Treat authenticity, ethics/representation, consent, safety, and factual context as conditional gates, not aesthetic scores. For every proposed action state:

- action;
- expected viewing effect;
- tradeoff;
- availability: now, similar scene, or rare event.

Give one prioritized reshoot action and distinguish what post-processing can and cannot repair. Add one 20–40 minute practice drill. Use observable landmarks or proportions instead of fake precision.

Treat the response structure as a silent quality check, not a visible report-writing style. Do not render the formal numbered audit in ordinary chat. Use the human voice rules in `references/response-card.md`: concrete nouns before jargon, one judgment at a time, scene-ready directions, natural uncertainty, and no generic praise.

### 5. Always show scores without false ranking

Always show the eight score intervals in the ordinary first response; do not hide them in expandable detail and do not drop them to make the voice feel conversational. Give 0–5 integer intervals for each applicable dimension: technical readability; framing/edge control; attention/formal organization; light/tone/color; space/layering; moment/key relationship; information/story/emotional response; expressive consistency/finish. Pair every interval with one short image-specific reason. Do not compute a total, percentile, “master score,” or rank across genres. Mark non-applicable dimensions `N/A`. Do not score presumed consent, ethics, authenticity, or factual accuracy. When comparable earlier critiques exist in the same genre and rubric version, mention a dimension trend; otherwise do not imply that one score proves progress.

### 6. Add references carefully

When web access exists, add at least one and at most two verified method references by default:

- Prefer a direct page for one named photograph. A project or article page is acceptable only when the answer identifies the exact photograph by author, title/location, and year, and tells the user where it appears on that page.
- Embed an individual image only when its license is verified as public domain, CC0, CC BY, or CC BY-SA; otherwise provide the official link only.

Never hand the user an undirected portfolio, exhibition, or search-results link. For every reference give a 20–60 second looking task, then explain the visible relation it addresses, what to inspect in that exact frame, one important difference from the user's photograph, and one transferable experiment. Fame is never scoring evidence. If source verification cannot be completed, omit the example instead of guessing.

### 7. Make crop and color advice visible when requested

When the user asks how the current file would look after cropping or color work, produce a non-destructive `裁切与调色示意` only after diagnosis. Show the source and treatment side by side when the surface allows. Make both parts independently legible: mark or describe the crop boundary, and ensure the proposed tone/color treatment changes at least two named visual relationships, such as wall-to-face brightness and neutral-to-saturated color competition. Preserve people, objects, gestures, text, and documentary content; change only crop and explicitly proposed tonal/color controls.

Inspect the result against the source. Reject and do not deliver a preview when the visible change is effectively crop-only, when the tonal claim cannot be seen, or when a generative tool changes people, text, objects, or gestures. In that case say that a faithful pixel-level preview is unavailable and give a crop boundary plus ordered adjustment recipe; never let a generated approximation impersonate a develop. Always list what the edit cannot repair.

### 8. Offer optional context review

End by inviting, not requiring, the user's purpose or intended meaning. A second pass may change intent fit, meaning, tradeoffs, or the recommended branch. It may not rewrite pixel facts. Name the new fact that changed the conclusion.

## Boundaries

- Use probability language for viewing effects and causal explanations.
- Do not assert identities, relationships, consent, staging, precise equipment/settings, location, or photographer from one image.
- Never promise that sharpening restores missed focus or that cropping restores off-frame information.
- Label object removal, relocation, or generation as compositing/generative editing when the use context requires disclosure.
- Do not recommend trespass, traffic exposure, interference with public events, or unsafe positioning.
- When a request is really an image edit, hand off to the available image-editing capability after the critique only if the user asked for the edit.

## Quality check

Before sending, verify every required field in the response card is present and every central claim points to visible evidence. Run the full adaptive observation bank silently, then the five-item miss audit one last time: eye/key-region focus, frame-edge cuts, background mergers or intrusions, tonal/color extremes, and crop/axis pressure. Verify that the public map selected rather than dumped dimensions, and that any contextual gate stayed outside the score. For a saved Markdown critique, run:

```bash
python3 scripts/validate_response.py /absolute/path/to/critique.md
```

The checker verifies structural completeness only; it cannot verify whether the visual judgment is correct.
