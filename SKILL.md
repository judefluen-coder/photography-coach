---
name: photography-coach
description: Evidence-based critique and deliberate-practice coaching for a user-supplied photograph, with an optional local visual report and faithful crop/color treatment. Use when the user uploads or points to a photo and asks whether it works, what is wrong, how to reshoot or edit it, how to improve composition/light/tone/story/portrait treatment, for a score or objective assessment, for a visual critique page, or for comparable masterwork/reference examples. Also use for a second-pass critique after the user reveals intent. Do not use for camera-shopping advice, generic photography lessons without a target image, image generation/editing without critique, or claims of authenticating authorship.
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
2. `references/integrity-preflight.md` for the mandatory six-family error-detection gate.
3. `references/response-card.md` for the user-facing output contract.
4. Read `references/reference-policy.md` and `references/knowledge-method.md` when giving an example image, photographer, course, or external link.
5. Search `references/critique-patterns.jsonl`, `references/masterwork-cards.jsonl`, and `references/source-registry.jsonl` with `scripts/search_knowledge.py` after diagnosis when a rule, exercise, course, or reference is needed. The search expands Chinese photography vocabulary through `references/search-aliases.json`; use the user's natural Chinese terms or two to four method tags. Do not load every record for every photograph.
6. Read `references/knowledge-status.json` before making any claim about knowledge-base coverage. While it says `bootstrap`, treat results as individually verified aids and continue targeted web verification; do not imply that the corpus is sufficient or representative.
7. Read `references/visual-report.md` when the user asks for an interface, visual page, downloadable treatment, or a reusable Codex-app presentation.

Never read `references/benchmark-cases.jsonl` during an ordinary critique or while producing a blind benchmark response. It contains holdout labels and answer keys. Use it only after a response is frozen for scoring or when maintaining the benchmark itself; follow `references/benchmark-method.md` in that mode.

## Workflow

### 1. Inspect before interpreting

Inspect the actual image at the highest useful resolution. If only a thumbnail, compressed screenshot, or inaccessible URL is available, state that limitation and lower confidence. Never infer invisible EXIF or off-frame events.

Before running any quantitative probe or ranking a fault, make a scene-topology snapshot from the pixels: count the important repeated units and visibly different states; trace one path or axis from start to end; find one exception or interruption; scan all four edges for unique objects and line endpoints; and locate a small or distant scale anchor when one exists. This snapshot prevents a strong statistic or a familiar scene label from replacing the actual arrangement of the frame.

When a local image file is accessible, run `python3 scripts/analyze_image_integrity.py /absolute/path/to/image --json` after that visual snapshot and before the six-family review. This probe measures pixel-level cues for tonal clipping, saturation/cast, weak detail, axis deviation, and edge-density imbalance. It nominates areas to inspect: a signal is not a defect verdict, a strong signal is not automatically the leading issue, and no signal is not a pass. If the probe raises a family, inspect that family at full useful resolution and do not mark it `通过` unless the response names a localized visual falsifier. If the probe cannot run, record why, continue the manual gate, and lower confidence for pixel-level claims.

### 2. Perform a blind first pass

Ignore title, author, award, source, likes, comments, and the user's intended meaning on the first pass. Record internally:

- tentative genre, with at most two candidates;
- visible-fact ledger using neutral object descriptions when identity is uncertain;
- frame-edge, tonal-extreme, key-region, depth-separation, and processing-artifact scan;
- an adaptive whole-frame scan covering all universal observation families in the standard, followed by any relevant genre module and non-scored contextual gate;
- first fixation, second destination, and core subject relationship;
- up to five bottleneck candidates with evidence, impact, repair value, intent dependence, and cost to the current strength.

Before any interpretation, run a fact-naming gate over every important noun, verb, and adjective. Keep conventional object classes only when contour, texture, and context support them. Rewrite unsupported roles, relationships, states, processes, emotions, meanings, seasons, weather, time, place, materials or contents, age or wear, causes, purposes, speed, and outcomes as visible descriptions or explicitly marked viewing hypotheses. Examples: `戴头盔的人`, not `工人`; `水面有气泡`, not `水正在沸腾`; `灰蓝天空`, not `阴天`; `粗糙石面`, not `古老磨损`; `瓶状容器`, not `啤酒`. A disclaimer in the final section does not cancel an earlier factual assertion.

Do not let a plausible story erase a visible technical or relational failure. Do not treat rule-breaking as a defect unless it obstructs the image's own core.

Before interpreting mood or story, complete the silent six-family gate in `references/integrity-preflight.md`: edge/crop pressure, shadow compression, highlight clipping, color excess/cast, roll/convergence with collateral crop, and detail damage. Compare the intended key region with adjacent detail at full useful resolution. Classify each family internally as `absent`, `plausible`, or `evidenced`; `evidenced` requires at least two independent observations. Record the strongest plausible objection and its falsifier even when the photograph basically works. Diagnose the visible state without inventing an editing history.

### 3. Choose exactly one decision class

- `STRUCTURAL_BOTTLENECK`: one evidenced issue clearly blocks the core reading and is worth fixing.
- `CONDITIONAL_BRANCH`: two defensible directions depend on purpose or would change the story's subject.
- `NO_STRUCTURAL_BOTTLENECK`: no candidate clears the evidence/impact/repair threshold; offer only an optional experiment with its cost.

Never invent a flaw merely to sound useful. Never hide a key-region failure behind “style.”

`CONDITIONAL_BRANCH` may resolve a genuine purpose fork, but it cannot absorb an execution issue that harms both branches. Fix or name that shared issue first. `NO_STRUCTURAL_BOTTLENECK` means “no rebuild required,” not “nothing could improve”: name one concrete watch item when a small, visible correction remains, and keep it clearly below the protected strength.

Before choosing any decision class, run a protection gate: name two different visible relationships that currently work, then name the specific information loss the proposed correction would recover and what it would cost those relationships. `STRUCTURAL_BOTTLENECK` requires a concrete, localized loss; a probe cue, convention violation, or preference without such a loss cannot justify rebuilding the frame. Before choosing `CONDITIONAL_BRANCH` or `NO_STRUCTURAL_BOTTLENECK`, also state internally the strongest integrity candidate, its two supporting observations, and the visible fact that would falsify it. If crop pressure, shadow compression, color excess, roll/collateral crop, highlight loss, or detail damage remains evidenced and has repair value under both intent branches, it must enter the public comparison, but it leads only when its recovered information or relationship value outranks the protected strength. Words such as “atmospheric,” “graphic,” “cinematic,” or “intentional” are not falsifiers on their own.

Expose the six-family result in `全画面看片地图` as the compact `完整性六检` table required by the response card. Every family must receive `通过`, `观察`, or `问题` plus a visible basis; do not mark a family `通过` merely because another flaw feels more interesting. Keep the adaptive map below it so the critique still prioritizes relationships, meaning, and strengths rather than becoming a defect checklist.

Record the scene-topology snapshot before `完整性量化：已运行（触发：家庭[强/复核]；无信号时写“无阈值信号”）` or `完整性量化：不可用（原因）`. The trigger list must match the probe rather than memory. Never copy the probe's threshold label into the verdict. Resolve it with visible evidence: a raised cue plus a localized failure supports `观察/问题`; a raised cue plus a localized falsifier may still support `通过`. In audit mode, make each family test concrete: compare opposite frame edges, two dark planes, two bright planes, two color/material regions, two independent stability references, and high-frequency textures at comparable scale across two depth planes. Add a four-edge/center ledger, three named key-region relationships, a three-lane relation coverage check, the protection gate, and a two-candidate priority adjudication using information loss, relationship damage, affected area, reversibility, repair value, and protection cost. The three relation lanes are edge/center, space/action, and light-color/material; each must compare two localized things and name the resulting reading. For action photographs, establish approach/contact/suspension/aftermath from the visible body-hand-foot-tool interface before discussing speed, outcome, or background colour. The probe strength routes attention but never settles priority: loss of a face, gesture, text, object identity, or material boundary may outrank a stronger but visibly organized color field, while a strong cue with no localized loss may remain only a watch item. A confirmed broad or key-region information loss enters candidate A and cannot be silently demoted below a reversible taste preference; if another candidate wins, record the localized counter-evidence and protection cost.

Use operation-specific falsifiers rather than generic reassurance. For roll, try a signed counter-rotation mentally or with a non-destructive preview: at least one reliable horizontal and one reliable vertical must improve together, and the resulting edge pressure must also improve, before calling the tilt repairable. Hills, roads, trees, curved facades, or one converging line are not enough. For crop pressure, test edge closure by comparing threatened-side room to the subject/action/repeated-module scale and to unrelated slack on the opposite side; literal edge contact is not required. For detail damage, check waxy smearing, halos or false microcontrast, and blocking or ringing, then compare high-frequency textures at similar apparent scale across two depth planes; do not use bokeh-versus-face softness as the sole comparison.

### 4. Build a prioritized whole-frame critique

Follow the default conversational mode in `references/response-card.md` unless the user explicitly asks for a formal report or export. Start with one decisive sentence, then expose a compact whole-frame map. Internally scan every universal family; publicly select the six to nine with the greatest explanatory or protective value. The map is not a checklist dump: for every selected family, name a visible relationship and its likely effect. Mark one `首要`, two to five `次要`, and at least one `要保护`; say `无明显问题` when an inspected family adds no useful criticism. Before fixing that priority, name the runner-up and compare the two by lost visible evidence and repair value, not by which criticism is easiest to phrase.

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

Treat reference selection as a fit gate, not a search result. A candidate is eligible only when it shares the leading diagnosis's photographic mechanism, the response can localize that mechanism in both images, a meaningful difference prevents recipe copying, and the user can transfer it into a concrete experiment. Similar subject matter, palette, mood, genre, or photographer fame is not enough. Give one reference by default; use two only when they teach genuinely different mechanisms.

Convert the diagnosis into two to four method tags and search the bundled knowledge base first. Prefer an admitted critique pattern and an exact masterwork card that clear the fit gate. The bundled cards are a verified starting set, not a closed catalogue: when no local candidate clears the gate and web access exists, search beyond the collection for a better exact photograph, verify its identity, direct page, visible method, and display rights, then use it without implying that it has already been admitted to the local corpus. If neither route yields a strong match, omit the reference and say why rather than attaching a famous but irrelevant image. Treat source tiers as provenance roles, not automatic truth weights: a creator may explain an idea clearly while the original photographer, work page, or curriculum remains the source of record. Re-open direct pages before delivery because links, course access, and rights can change.

In benchmark/audit runs with local knowledge assets, an exact-work reference is mandatory rather than optional. Use an admitted, verified masterwork card that matches the diagnosed relation and include the response-card comparison fields. A frozen benchmark response with only the omission sentence is structurally invalid.

### 7. Make crop and color advice visible when requested

When the user asks how the current file would look after cropping or color work, produce a non-destructive `裁切与调色示意` only after diagnosis. Show the source and treatment side by side when the surface allows. Make both parts independently legible: mark or describe the crop boundary, and ensure the proposed tone/color treatment changes at least two named visual relationships, such as wall-to-face brightness and neutral-to-saturated color competition. Preserve people, objects, gestures, text, and documentary content; change only crop and explicitly proposed tonal/color controls.

Inspect the result against the source. Reject and do not deliver a preview when the visible change is effectively crop-only, when the tonal claim cannot be seen, or when a generative tool changes people, text, objects, or gestures. In that case say that a faithful pixel-level preview is unavailable and give a crop boundary plus ordered adjustment recipe; never let a generated approximation impersonate a develop. Always list what the edit cannot repair.

### 8. Render a local visual report when the surface supports it

When the user asks for a visual page or has chosen the Codex-native visual workflow, map the completed critique to `references/visual-report.md` and run `scripts/render_visual_report.py`. Treat the page as a presentation layer, not a second diagnosis: its judgment, priority, scores, edit limits, and reference must match the chat critique.

Write report JSON and rendered files to a task-specific directory outside this skill repository. Never add a user photograph, treatment, report JSON, or rendered report to Git. If a faithful treatment exists, make it the default hero view, show the source beside it later, and provide both downloads. If no treatment passed source comparison, omit treatment controls instead of showing a simulated result.

Open the rendered page and inspect one desktop and one narrow layout before delivery. Keep the chat response self-contained and concise because the page is an optional durable view, not a substitute for the answer.

### 9. Offer optional context review

End by inviting, not requiring, the user's purpose or intended meaning. A second pass may change intent fit, meaning, tradeoffs, or the recommended branch. It may not rewrite pixel facts. Name the new fact that changed the conclusion.

## Boundaries

- Use probability language for viewing effects and causal explanations. `视觉上让人联想到……` may preserve an interpretation; it does not convert that interpretation into a fact.
- Do not assert identities, roles, relationships, consent, staging, emotion, intention, process, speed, outcome, weather, season, time, precise equipment/settings, location, photographer, material contents, taste or freshness, age or wear, cause, purpose, or symbolic meaning from one image. Describe the visible cue first and mark any useful interpretation as uncertain.
- Audit the assertion where it first appears. A late `未知` sentence never repairs an earlier unqualified claim.
- Never promise that sharpening restores missed focus or that cropping restores off-frame information.
- Label object removal, relocation, or generation as compositing/generative editing when the use context requires disclosure.
- Do not recommend trespass, traffic exposure, interference with public events, or unsafe positioning.
- When a request is really an image edit, hand off to the available image-editing capability after the critique only if the user asked for the edit.

## Quality check

Before sending, verify every required field in the response card is present and every central claim points to visible evidence. Run the full adaptive observation bank, fact-naming gate, and six-family integrity preflight silently one last time. Confirm that every `evidenced` family has two observations and is either prioritized or explicitly falsified; confirm that a purpose branch did not hide a shared execution issue. Verify three distinct relation lanes, scan every factual assertion where it first appears, and confirm that a late uncertainty note is not doing retroactive repair. Verify that the public map selected rather than dumped dimensions, and that any contextual gate stayed outside the score. For a saved Markdown critique, run:

```bash
python3 scripts/validate_response.py /absolute/path/to/critique.md
python3 scripts/validate_knowledge.py
```

For a benchmark response, run `python3 scripts/validate_response.py --benchmark /absolute/path/to/critique.md`; benchmark mode also requires a completed integrity probe and one exact-work reference.

The checkers verify structural completeness and knowledge cross-references only; they cannot verify whether the visual judgment or source interpretation is correct.
