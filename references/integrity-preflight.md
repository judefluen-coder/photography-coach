# Six-family integrity preflight

Use this compact preflight on every finished photograph before interpreting mood, symbolism, or likely intent. It is an error-detection layer, not a universal style prescription. Test visible state only; do not claim that a particular slider, lens, crop, or generative process caused it.

For each family, record internally `absent`, `plausible`, or `evidenced`. `Evidenced` requires at least two independent observations. One vague impression is not enough.

## Quantitative attention probe

When the image is a local file, first run `python3 scripts/analyze_image_integrity.py /absolute/path/to/image --json`. Record whether it ran. Its thresholds are intentionally asymmetric: they are designed to make the reviewer look again, not to certify failure or quality.

- A raised signal must be resolved at full useful resolution. Do not answer it with mood words or a generic claim that detail remains.
- A family may be marked `问题` or `观察` when one measured cue and one localized visible sign agree; two localized visible signs remain sufficient without a measured cue.
- A raised signal may still be marked `通过`, but only with a localized falsifier—for example, the clipped pixels are confined to pin-point speculars while two named important bright surfaces retain texture.
- No signal never proves `通过`. Crop pressure, subject-specific clipping, local colour contamination, and intentional/non-intentional roll often need semantic visual inspection that whole-image statistics cannot perform.
- Never expose a raw metric dump unless the user asks. Translate only the cue that changes the diagnosis into visible photographic language.
- In an audit response, transcribe the probe's family and strength exactly as `触发：暗部[强]、轴线/透视[复核]`; write `无阈值信号` only when the probe returned none. This binds the manual review to the image that was measured.
- Use paired visible comparisons rather than assurances: `对边：左…与右…`, `暗面：…与…`, `亮面：…与…`, `色彩对照：…与…`, `参照：…与…`, and `同尺度：…与…`. These labels are audit rails, not wording required in ordinary conversation.
- When one or more `强` cues remain `观察/问题`, the single public `首要` must address at least one of those families. A strong cue may be marked `通过` only with localized counter-evidence in the same line; generic phrases such as “仍有层次” do not falsify it.
- Exception: a `轴线/透视[强]` cue is derived from agreeing horizontal and vertical edge populations, so it cannot be marked `通过`. Mark the visible tilt `观察` or `问题`, then decide whether it is an intentional organizing choice or a repairable roll.

## 1. Edge and crop pressure

- Compare opposite-edge intervals, not one isolated cut. Look at repeated spacing, limbs, line endpoints, circles, faces, signage, wings, and directional space.
- Ask whether one side feels enlarged, crowded, or abruptly amputated while the opposite side retains unrelated slack.
- Distinguish a decisive fragment that expands off-frame space from a timid cut that only removes evidence.
- Falsifier: the cut completes a visible rhythm or relation, direction has usable continuation space, and opposite edges carry comparable intentional tension.

## 2. Shadow compression

- Inspect the two or three largest dark regions and at least one key dark boundary at thumbnail and full useful resolution.
- Check whether unrelated materials—hair, clothing, furniture, foliage, wall, water—collapse to nearly the same featureless value.
- Separate a chosen silhouette from global black-point compression: a silhouette can stay closed while other dark planes retain different edges or textures.
- Falsifier: required boundaries remain readable, multiple dark materials still separate, and closed blacks are localized to the image's stated visual logic.

## 3. Highlight clipping

- Check the brightest repeated surfaces, skin patches, clouds, reflections, lamps, signs, and pale objects for retained edge, texture, and color variation.
- Distinguish a small specular point from a broad pale region whose shape or material is needed.
- Falsifier: clipping is confined to plausible speculars or intentional white fields while adjacent important highlights retain form.

## 4. Color excess or cast

- Find likely neutral or low-chroma anchors and compare them across the frame; avoid assuming an object's real-world color when uncertain.
- Check whether several unrelated surfaces drift toward the same warm/cool hue, or whether saturated areas lose internal hue/value variation.
- Compare the color treatment's structural job with a neutral mental alternative: does it separate planes and guide attention, or merely coat everything with mood?
- Falsifier: repeated surfaces retain distinct hue/value relationships, neutral anchors are coherent with the light, and saturation has a clear hierarchy.

## 5. Roll, convergence, and collateral crop

- Use at least two independent stability references: a true horizon, waterline, hanging vertical, repeated architecture, door frame, or other plausibly level/plumb structure.
- Separate camera roll from sloping ground and normal perspective convergence. Never level from a single uncertain line.
- Check whether the suspected roll co-occurs with squeezed corners, uneven headroom, clipped geometry, or lost trajectory space. Co-occurrence strengthens the candidate.
- Falsifier: independent references agree with the frame, the directional tilt is repeated elsewhere, and edge pressure does not look like collateral loss.

## 6. Detail damage

- Compare the key region with nearby high-frequency texture at the same apparent scale.
- Look for halos, block boundaries, waxy smearing, false microcontrast, ringing, banding, or noise reduction that selectively erases required detail.
- Do not infer whether softness came from focus, motion, shake, denoising, resizing, or platform compression when the finished image cannot distinguish them.
- Falsifier: texture falls off consistently with depth or motion, edges remain natural, and the key region is at least as readable as comparable nearby detail.

## Priority and wording gate

If a family is evidenced and weakens the core under every plausible intent branch, place it in the candidate ledger. If correcting it has meaningful repair value and low cost to the protected strength, it must be the public leading correction or the response must explicitly explain why another issue has greater repair value.

Use wording such as “画面目前呈现为……”“这两个位置共同支持……”“若原文件仍有层次，可尝试……”. Avoid “你一定拉黑了”“这是某个预设造成的” or other claims about invisible provenance.
