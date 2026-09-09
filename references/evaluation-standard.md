# Evaluation standard v1.6

This standard was revised through multiple pilots, development replays, and two valid source-disjoint 100-case holdouts, followed by an invalidated v4 attempt. v1.2 passed 63/100 on holdout v2, with 70% observation recall and 52% degraded-variant detection. The v1.4 revision added materialized-image answer-key audits, stronger localization, and explicit priority adjudication. On the untouched holdout v3 completed September 8, 2026, it passed 57/100, recalled 77% of required observations, detected 84% of derived failures, and overcorrected 16% of acclaimed controls. v1.5 added sentence-local fact naming, three-lane relationship coverage, and an information-loss gate. A 100-case development replay on the already-seen v3 images reduced hallucination violations from 19% to 1% and raised raw case pass from 57% to 63%, but observation recall fell to 68.3%, degraded-variant detection to 64%, and detail/tilt/crop recognition remained weak. v1.6 therefore puts a scene-topology snapshot before quantitative cues, makes probe strength a nomination rather than a priority rule, adds operation-specific tilt/crop/detail tests, and requires a two-relation protection gate before structural correction. The attempted v4 evaluation cannot certify those changes: all three v4 runs reused the same stale materialized image set, and comparison with the current case records found 97/100 source-SHA-1 mismatches, 66/100 quality-band mismatches, 76/100 genre mismatches, and 43/100 variant-recipe mismatches. Its raw metrics remain in `benchmark-report.json` for history only and are non-evidentiary. Current and historical reports are preserved in `benchmark-development-report.json`, `integrity-sentinel-report.json`, `benchmark-v13b-development-report.json`, `benchmark-v3-report.json`, and `benchmark-report.json`. v1.6 requires a newly sourced, source-disjoint holdout with verified image-to-case identity binding. The standard remains a research prototype: it must not be described as objective truth, expert certification, proven learning improvement, or release-ready.

The v0.9 taxonomy is also calibrated against two external practices: the Getty Museum's progression from description to reflection and formal analysis, including first fixation, viewer response, intent, and surprise; and World Press Photo's separation of visual quality/story from representation, authenticity, context, accountability, and ethics. These sources inform coverage and boundary design, not universal taste rules:

- https://www.getty.edu/education/for_teachers/curricula/exploring_photographs/lesson03.html
- https://www.worldpressphoto.org/contest/judging-process
- https://www.worldpressphoto.org/contest/code-of-ethics
- https://www.worldpressphoto.org/contest/verification-process

## Claim types

Keep these categories distinct:

| Code | Claim | Required wording |
|---|---|---|
| F | Visible fact | Direct, localized description |
| E | Viewing effect | Probabilistic: “may,” “tends to,” “likely” |
| I | Intent/use condition | Explicit “if the goal/use is…” branch |
| P | Preference | Parallel options, not a universal rule |

Do not infer author, identity, role, relationship, motivation, emotion, consent, staging, exact location, weather, season, time of day, equipment, exposure settings, lighting gear, camera position, before or after action, process, speed, outcome, material contents, taste or freshness, age or wear, cause, purpose, symbolism, or the precise cause of softness from one finished image.

### Fact-naming audit

Audit a claim where it first appears, not only in a closing disclaimer. For each role/relationship, state/process, feeling/meaning, and place/time/cause label, choose one of three treatments:

1. **Visible description:** location, contour, surface, colour, posture, contact, interval, or direction that the image directly supplies.
2. **Viewing hypothesis:** an explicitly uncertain reading such as “视觉上让人联想到……”, followed by the visible cue and at least one live alternative.
3. **Verified context:** information supplied by a trustworthy caption or user, kept separate from the blind pixel reading.

An unqualified assertion followed later by “身份未知” remains an assertion and fails the boundary. Common traps include reading foliage colour as season, gray sky as weather, lighting as time, bubbles as cooking, a bottle as its contents, roughness as age, clothes as occupation, size as kinship or age, gesture as emotion, and splash or blur as speed.

### Ambiguous objects

- Name an object only when contour, texture, and context jointly support it.
- If partly hidden, defocused, or fragmentary, begin with shape and location: “pale curved foreground form,” “dark soft-edged block at the bottom.”
- If the name affects causality, include an alternative explanation.
- Later context may update the name but never rewrite the original pixel fact.

## Genre routing and key regions

| Genre | Core relationship | Mandatory key regions | Avoid mechanical rules |
|---|---|---|---|
| Street/documentary/travel | gesture, gaze, spacing, environment, timing, representation | action interface, face/gesture, subject-background boundary, contextual clues | background need not be blurred or spotless |
| Portrait/environmental portrait | gaze, pose, face modeling, person-place relationship, use | nearer eye, both hands, included body/clothing area | commercial headshot lighting is not universal |
| Landscape | depth, weather, scale, path | horizon/major boundaries, spatial layers, tonal endpoints | lack of people is not a defect |
| Architecture | geometry, repetition, scale, material, use traces | main axis, edges, repeated units, perspective intersections | convergence need not be corrected |
| Still life/product/food/macro | focus plane, material, color fidelity, object hierarchy, shape rhythm | focus plane, contour, surface texture, label/action interface | shallow depth or stylized color is not automatically wrong |
| Wildlife/sports/action | behavior, action phase, anticipation, separation, safety | eye/face, action interface, limb/edge junction, trajectory space | the most frozen frame is not automatically the best moment |
| Concept/composite | transformation rule, element consistency, viewing logic | composite edges, light direction, scale, shape interfaces | documentary realism cannot veto intentional synthesis |
| Series/photo essay | selection, order, pacing, transition, redundancy, context | opener/closer, repeated motifs, missing bridge, caption-image relation | every frame need not work as a standalone single |

Keep at most two genre candidates when uncertain and say which judgment changes with the routing.

## Mandatory topology-first scan

### Pass 0: scene topology before defect search

Before viewing probe results or ranking any correction, build a compact map of what is actually arranged in the frame:

1. Count the important repeated units and separate their visibly different states or orientations.
2. Trace one dominant path or axis from a named start to a named endpoint; do not replace the path with a list of objects.
3. Find one exception, interruption, or missing link in the repetition/path, including the honest result `none visible`.
4. Scan all four edges for unique objects, line endpoints, clipped modules, and directional continuation.
5. Name one small or distant scale anchor when present; otherwise state that no reliable scale anchor is visible.

This pass is descriptive. It precedes the quantitative attention probe so a statistical cue cannot rewrite the number, state, path, edge, or scale relations already visible in the photograph.

### Pass A: low-level and key-region scan

Use this fixed order:

1. Four corners and edges: intrusions, awkward truncation, bright spots, marks.
2. Three extremes: brightest, darkest, and most saturated regions; test unintended competition.
3. Subject key regions: focus, occlusion, action interface, eyes/hands/text readability.
4. Spatial layers: mergers and lines/bright patches cutting important contours.
5. Processing traces: color noise, banding, halos, masking residue, oversharpening, crushed blacks, clipped highlights.

For every image, silently answer these concrete miss checks before moving to meaning:

1. Is the intended eye, face, hand, action interface, product surface, or other key region at least as readable as nearby secondary detail?
2. Do fingers, feet, tools, text, or important shapes meet an edge in a way that looks accidental?
3. Does a large reflection, pole, branch, sign, bin, white patch, or background line interrupt the main relation?
4. Is the tightness or empty area doing visible work, and are horizon or architectural axes internally deliberate?
5. Do the brightest, darkest, or most saturated areas support the first two fixations rather than create a third unrelated target?

After Pass 0, when a local file is accessible, run `scripts/analyze_image_integrity.py` as specified in `integrity-preflight.md`. Its output is an attention router, not a quality score or priority vote: it can expose pixel-distribution or edge-structure cues that the visual model otherwise rationalizes away, but it cannot determine subject importance, intention, whether a crop is meaningful, or whether a visibly tilted structure should be corrected. Then run the six-family integrity challenge. Test each family as a falsifiable hypothesis and classify it internally as `absent`, `plausible`, or `evidenced`. A style explanation is not a result: it is a counter-condition that must be tested against the visible state. Diagnose what the image shows, not an unobservable editing history.

In an audit response, record the scene-topology snapshot before whether the quantitative probe ran, then expose the completed scan as a compact `完整性六检` table before the adaptive whole-frame map. Give one line each for edge/crop, shadows, highlights, color, axis/perspective, and detail. Use only `通过`, `观察`, or `问题`; every line needs a short visible basis. `观察` or `问题` needs two localized signs, or one measured cue plus one localized sign. A raised cue can still be falsified, but a `通过` verdict must name that visible falsifier. This table is evidence that the scan ran, not six mandatory faults. It does not replace the prioritized whole-frame map. In ordinary conversation, fold the topology into concrete prose instead of exposing another template.

An integrity candidate becomes `evidenced` only with at least two independent observations, for example two opposite edges, two unrelated dark regions, repeated nominal neutrals, or one stability reference plus collateral edge pressure. If the same evidenced issue weakens the core under both plausible intent branches, it must enter the candidate ledger and cannot be demoted merely because the subject, moment, or graphic idea still works.

Do not infer the cause of softness from a finished image. Compare relative readability and say that focus, motion, shake, denoising, or compression may be indistinguishable.

A key-region coverage failure must enter the candidate ledger when any of these occurs:

- portrait eyes, face, hands, or a visually dominant included body/clothing area lose task-required readability;
- an action interface such as person–ball, hand–tool, foot–ground is hidden or merged;
- two or more major landscape layers merge through blocked shadows, clipped highlights, or insufficient separation;
- an architectural axis or repeated unit is interrupted by a high-salience intrusion;
- a concept depends on a shape, scale, or light relation that is inconsistent.

### Pass B: attention, relationship, and meaning

Ask in order: Where does the first fixation land? Can the eye reach the core next? Is the key relationship readable? Does the environment add needed context? Are formal choices internally consistent? What changes if the main element disappears?

Before ranking, complete three different relation checks: (1) an edge or centre relation, (2) a depth, overlap, contact, or action relation, and (3) a light, colour, or material relation. Each check must name two localized things and the effect of their relation. Three isolated object labels do not count. Reconcile these checks with Pass 0: repeated-unit counts, path endpoints, exceptions, edge objects, and scale anchors may not silently change. In action frames, decide whether the visible interface shows approach, contact, suspension, or aftermath before using words about speed, force, or outcome.

An abstract interpretation may justify a technical cost, but cannot erase the Pass A observation.

### Adaptive observation bank

The user's examples are prompts, not an exhaustive checklist. Before ranking candidates, silently scan every universal family below, then activate genre modules and boundary gates only when relevant. A family may be strong, weak, neutral, or not applicable. Do not manufacture a fault or expose the whole bank as a vocabulary dump.

1. **Capture and technical integrity:** key-region readability, focus/motion ambiguity, exposure latitude, dynamic range, noise, compression, flare, and processing artifacts.
2. **Framing and edge control:** aspect ratio, placement, negative space, crop pressure, visual-weight distribution, edge intrusions, and accidental truncations.
3. **Attention hierarchy and eye path:** first, second, and third fixations; salience competitors; whether the eye can reach the core relation and return.
4. **Formal organization:** balance and tension, line, shape, mass, proportion, rhythm, repetition, symmetry/asymmetry, tangent, and interval.
5. **Light and tone:** direction, quality, contrast hierarchy, local separation, highlight/shadow roles, luminosity continuity, and tonal endpoints.
6. **Color:** palette, temperature, harmony/discord, color anchors, saturation hierarchy, casts, color separation, and color's narrative or symbolic job.
7. **Space and figure-ground:** foreground/midground/background, overlap, occlusion, sharp/soft transitions, depth cues, atmospheric depth, and subject-background separation.
8. **Scale, distance, and perspective:** relative size, cluster spacing, camera-to-subject distance, convergence, spatial compression, and near/far cues.
9. **Moment and time:** gesture, gaze, action phase, motion, anticipation/aftermath, duration, coincidence, and whether another instant would change the relation.
10. **Subject–object–environment relationships:** person-to-person distance, action interfaces, object clues, setting, group structure, inclusion/exclusion, and empty intervals.
11. **Information, meaning, and response:** information density, redundancy, narrative inference, emotional temperature, ambiguity, surprise, cultural cues, and what disappears if an element is removed.
12. **Intent, coherence, voice, and presentation:** fit to stated or likely use, consistency between form and meaning, cliché versus transformation, editing restraint, output/display, and—when multiple images exist—selection and sequence.

Some pairs must be checked separately even if the public score later combines them: light/tone versus color; framing versus formal organization; space versus perspective; moment versus subject relationship; intended meaning versus the viewer's observable response.

For user-facing synthesis, select the six to nine families with the greatest explanatory or protective value and rank observations rather than listing jargon:

- one `首要`: the relation with the highest repair value;
- two to five `次要`: real but lower-priority relations;
- at least one `要保护`: a current strength an edit or reshoot could damage;
- `无明显问题` for an inspected axis that yields no useful issue.

A single priority is not permission to suppress the rest of the frame. Conversely, the whole-frame map is not permission to manufacture twelve faults. Merge adjacent families only when the same visible relation genuinely explains them.

### Contextual gates: inspect, but do not turn them into taste scores

- **Authenticity and disclosure:** for documentary, news, scientific, wildlife, or evidentiary uses, ask about staging, captions, composites, object removal, and generative edits when they could change meaning. Do not infer them from pixels alone.
- **Ethics and representation:** check dignity, vulnerability, stereotyping, power, consent, privacy, possible harm, and the photographer's influence on the scene. Flag a contextual question or risk; do not numerically grade a person's dignity or presumed consent.
- **Safety and access:** do not reward a frame for trespass, traffic exposure, wildlife disturbance, or coercive proximity.
- **Factual context:** captions, place, date, identities, and sequence may change a documentary reading. Keep the blind formal pass, then allow a contextual second pass.

## Candidate ledger

List up to five internal candidates. For each, record:

- object/relationship and at least two positional observations;
- impact 0–3;
- evidence strength 0–3;
- repair value 0–3;
- intent dependence 0–2;
- cost to an existing strength 0–2;
- layer: technical, low-level execution, attention, key relationship, or meaning/form.

Use `impact + evidence + repair value - intent dependence - strength cost` only as a thinking aid, never as a public objective score.

Apply three constraints:

1. A two-observation key-region failure must be compared directly with any style explanation.
2. Style is considered after readability and relationship. Grain, tilt, dark treatment, selective color, and shallow depth are defects only when execution is inconsistent, a key region is lost, or the use conflicts.
3. For the leading candidate, state an image fact that would falsify it. If none exists, it is probably preference.

Apply two additional constraints from the v0.6 holdout:

4. **Branch does not erase shared defects.** A purpose-dependent fork may protect blur, darkness, context, tilt, or negative space, but an edge cut, focus miss, intrusive object, or processing excess that weakens both branches stays in the ledger and may outrank the fork.
5. **Separate severity from existence.** Classify the best-supported issue internally as `rebuild`, `correctable`, or `preference`. A correctable issue may be mentioned without declaring the whole image structurally broken; a minor but concrete adjustment must not disappear merely because the core works.

Apply two integrity constraints from the 100-case blind baseline:

6. **Whole-frame defects outrank purpose forks when both branches pay the cost.** Uneven crop pressure, global shadow compression, pervasive color excess, or camera roll with collateral edge loss is not resolved by choosing “documentary” versus “expressive.” First state the common visible cost; branch only on how much to correct it.
7. **A technical candidate needs an exit test, not a reassuring adjective.** Before rejecting the strongest integrity candidate, name the observation that disproves it: retained separation in multiple dark materials, stable independent axes, balanced opposite-edge intervals, or preserved hue/value variation in repeated surfaces. “Atmospheric,” “graphic,” “cinematic,” and “intentional” do not count as falsifiers by themselves.

Apply three constraints from the v3 failure analysis:

8. **Confirmed information loss is candidate A.** When a broad region or key interface loses readable highlight, shadow, detail, geometry, edge continuation, or material colour, compare it before any reversible taste adjustment. It can lose priority only when localized counter-evidence shows the core relation survives and another repair has greater information or relationship value.
9. **Direction space is not edge contact.** A person, animal, vehicle, line, or repeated module can be crop-pressured without touching the frame. Compare continuation and closure on opposite edges, including unrelated slack elsewhere.
10. **Fact boundaries are sentence-local.** A closing unknowns list cannot repair unsupported roles, relationships, states, emotions, time, weather, process, speed, or causality already asserted as facts.

Apply five constraints from the v1.5 development replay:

11. **Topology precedes cue strength.** Count repeated units and states, trace one start-to-end path, name an exception, scan edge endpoints, and find a scale anchor before reading the probe. If the later diagnosis contradicts that snapshot, revisit the pixels rather than rationalizing the contradiction.
12. **Probe cues nominate; visible loss ranks.** `强` and `复核` determine where to inspect, never what must be `首要`. A family leads only after localized evidence shows lost information or a broken relationship with useful repair value.
13. **Tilt needs a signed counter-rotation test.** Call roll repairable only when one reliable horizontal and one reliable vertical improve together under the same counter-rotation and the edge-pressure result also improves. A hill, road, tree, curved facade, or one converging line is insufficient. A strong axis statistic may be marked `通过` when localized references falsify common roll.
14. **Crop and detail need operation-specific tests.** For crop pressure, compare threatened-side room to body/action/module scale and unrelated opposite-side slack; no literal cut is required. For detail damage, test waxy smearing, halo or false microcontrast, and blocking or ringing, then compare high-frequency textures of similar apparent scale across two depth planes. Bokeh versus a face is not sufficient by itself.
15. **Protect before correcting.** Before `STRUCTURAL_BOTTLENECK`, name two currently successful relations, one concrete information loss, and the proposed correction's cost to both relations. Without a localized loss, keep the issue as observation, purpose branch, or optional experiment.

## Decision rules

### STRUCTURAL_BOTTLENECK

Use only when the issue has at least two positional observations, names a concrete information or relationship loss, blocks the core reading, promises more repair value than loss to two named current strengths, is not merely a broken convention, and clearly leads the ledger. State why it outranks the runner-up.

### CONDITIONAL_BRANCH

Use when either direction is defensible and the choice depends on use or changes the story subject. Mandatory examples include:

- the top two candidates differ by no more than one ledger point and imply different story subjects;
- contextual background versus isolated subject;
- negative space versus tight crop;
- pure silhouette versus shadow detail;
- selective color, compositing, or object removal under documentary versus art/commercial use;
- later context could flip a current strength into a problem, or vice versa.

For both A and B give target, action, effect, and cost. Do not declare a winner without the missing purpose.

### NO_STRUCTURAL_BOTTLENECK

Use only when no candidate reaches impact ≥2, evidence ≥2, repair value ≥2, intent dependence ≤1, and strength cost ≤1. Explicitly check key-region readability, visible low-level error, high-salience competition, and all six integrity families. Before choosing this class, name internally the strongest integrity candidate, its two best supporting observations, and its falsifier. If it remains evidenced and correctable, it must appear publicly as the leading correction even when the image does not need a rebuild.

Use this protection statement:

> 当前没有需要重构的瓶颈。下面是可选实验，不代表现有做法错误；实验会同时说明牺牲的当前优点。

Then name the strongest concrete watch item and explain in one sentence why it remains `correctable` rather than `rebuild`. This prevents “protection” from becoming a blanket dismissal of visible focus, crop, background, or processing issues.

## Advice constraints

Every action includes action, expected viewing effect, tradeoff, availability (`即时`, `相似场景`, or `稀有事件`), and a 20–40 minute alternative drill if it is not immediately available.

- Exposure-setting advice must name the compensating change needed to hold exposure.
- Sharpening cannot restore truly missed focus.
- Denoising trades texture; lifting shadows may amplify noise and color casts.
- Cropping cannot restore off-frame content and reduces pixel count.
- Background blur depends jointly on aperture, focal length, camera distance, and subject-background distance.
- A finished image rarely distinguishes shake, subject motion, missed focus, denoising, and platform compression with certainty.
- Object removal/movement/generation is a composite or generative edit and may require disclosure.
- Advice must not require unsafe or unauthorized access.

## Crop and color preview constraints

When a visual treatment preview is requested:

- preserve the source non-destructively and label the output `裁切与调色示意`;
- show source and treatment together when possible so crop and color claims can be checked;
- change only crop, exposure, contrast, highlight/shadow balance, white balance, saturation, and local tonal emphasis explicitly named in the critique;
- do not add, remove, relocate, reconstruct, beautify, or alter people, objects, text, or gestures unless the user separately requests a disclosed generative/composite edit;
- list the visible landmarks used for the crop and the adjustment order;
- state the tradeoff and what the treatment cannot recover, such as missed timing, hidden gesture, lost focus, or off-frame information.
- compare the preview with the source; reject it if the promised tonal/color differences are not visibly inspectable or if a generative editor alters text, anatomy, objects, gestures, or fine detail. Give the exact recipe instead of delivering a misleading approximation.

## Dimension intervals

Always show integer intervals from 0–5 in the ordinary response and give one image-specific reason per dimension. Use no overall score. The stable public dimensions are broader than the observation bank so results remain readable and comparable:

- technical readability;
- framing and edge control;
- attention and formal organization;
- light/tone/color;
- space and layering;
- moment and key relationship;
- information/story/emotional response;
- expressive consistency and finish.

State purpose fit as a conditional branch when the intended use is unknown. Treat originality/voice as a named observation inside expressive consistency, not a penalty for failing to resemble famous work. Ethics, consent, authenticity, safety, and factual context remain non-scored gates. Use `N/A` when a dimension genuinely does not apply.

Anchors: 0 absent/contradictory; 1 severe problem dominates; 2 problems outweigh strengths; 3 basically works; 4 choices mostly reinforce one another; 5 highly unified. Use `N/A` when irrelevant. Do not rank unlike genres.
