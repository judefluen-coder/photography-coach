# Evaluation standard v1.0

This standard was revised from a 10-case pilot, a preregistered 30-case public-consensus benchmark, a 30-case v0.6 holdout, and a clean-context 100-case v0.9 blind baseline completed on September 6, 2026. The blind baseline passed 83/100 cases and recalled 94.33% of required observations, but detected only 40% of deliberately degraded variants. Its repeated misses were crop pressure, shadow compression, color excess, and small roll-plus-crop changes. The standard therefore remains a research prototype: it must not be described as objective truth, expert certification, proven learning improvement, or release-ready.

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

Do not infer author, identity, relationship, motivation, consent, staging, exact location, equipment, exposure settings, lighting gear, camera position, before/after action, or the precise cause of softness from one finished image.

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

## Mandatory two-pass scan

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

Then run the six-family integrity challenge in `integrity-preflight.md`. Test each family as a falsifiable hypothesis and classify it internally as `absent`, `plausible`, or `evidenced`. A style explanation is not a result: it is a counter-condition that must be tested against the visible state. Diagnose what the image shows, not an unobservable editing history.

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

## Decision rules

### STRUCTURAL_BOTTLENECK

Use only when the issue has at least two positional observations, blocks the core reading, promises more repair value than loss to the current strength, is not merely a broken convention, and clearly leads the ledger. State why it outranks the runner-up.

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
