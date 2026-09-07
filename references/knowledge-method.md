# Knowledge base method

Use this file when adding, selecting, or interpreting theory, courses, creator material, or masterwork references. The knowledge base supports critique; it does not define universal taste.

## Maturity gate

Read `knowledge-status.json` before describing the database's maturity. While its stage is `bootstrap`, every record is an individually useful aid but the collection is not broad enough to support claims of representative coverage. Do not call it a completed or sufficient knowledge base. Continue open-source verification around any search result and run `python3 scripts/validate_knowledge.py --release` before changing the stage to `release-candidate`.

The release threshold is a floor, not proof of quality. Every numerical threshold and every coverage floor in `knowledge-status.json` must pass. Coverage is counted from explicit record metadata rather than inferred from titles. The minimum-host floor prevents one publisher or platform from satisfying the corpus by itself. Raw bulk imports, duplicate mirrors, collection hubs presented as single works, and several crops of one photograph do not count as distinct teaching cards.

The active 100-case holdout v2 is governed by `benchmark-method.md`; the earlier source set is retained as `benchmark-development-cases.jsonl`. Passing source, masterwork, and rule counts does not change the stage by itself: all active benchmark images must materialize, the blind responses must be scored by band and genre, and the published result must include failures. Never search `benchmark-cases.jsonl` while critiquing a benchmark image; that file is an answer key, not coaching evidence.

## Source roles and weight

| Tier | Source role | Appropriate use | Never assume |
|---|---|---|---|
| 1 | Photographer/estate, museum/archive, original curriculum, contest standard | identity, title/date, stated practice, curriculum, ethics, exact work page | institutional status makes every aesthetic claim universal |
| 2 | Structured course or specialist publication with named authorship | pedagogy, exercises, terminology, worked interpretation | paid access, prestige, or completeness proves effectiveness |
| 3 | Established educator/creator or translated/curated channel | accessible explanation, recurring learner problems, exercise ideas, discovery | audience size, fluency, or production value establishes authority |
| 4 | Community, ranking, comments, platform metrics | discovery, common misconceptions, vocabulary, product demand | popularity is evidence that a photograph or rule is good |

Use lower-tier material to discover a claim, then seek the photographer, work, institution, or original course behind it. Preserve disagreements rather than averaging them into a false consensus.

## Admission rule

Promote a claim into a critique pattern only when it has:

1. a visible condition that can be checked in a photograph;
2. at least two reasonably independent sources, including one Tier 1 or Tier 2 source when available;
3. one exact photograph or sequence that demonstrates the method;
4. a counter-condition showing when the opposite choice can work;
5. a scene-ready action or bounded exercise;
6. a declared scope: cross-genre heuristic, genre convention, use requirement, or preference.

Do not promote a creator's slogan, a platform ranking, a rule-of-thirds recipe, or an unattributed quote on its own.

## Record types

### Source record

Required fields in `source-registry.jsonl`:

- `id`, `kind`, `tier`, `title`, `author_org`, `url`;
- `language`, `access`, `status`, `use_for`;
- `source_lanes`, using only the controlled lane names in `knowledge-status.json`;
- `evidence_scope`, `limitations`, `reviewed_on`.

`status` is one of `verified`, `partial`, or `discovery_only`. Verified means the direct page was inspected and supports the stated scope, not that every claim on it is true.

### Masterwork card

Required fields in `masterwork-cards.jsonl`:

- exact identity: `photographer`, `title`, `year`, `direct_url`, `source_org`;
- routing: `genres`, `method_tags`;
- coverage: `coverage_genres`, `creator_regions`, `historical_period`, `tradition_tags`;
- `analysis_notes`, `teaching_use`, `anti_imitation`;
- `rights`, `verification_status`, `reviewed_on`.

`analysis_notes` are the coach's visible-reading notes, not claims attributed to the source. Never copy or embed an image unless the exact page verifies an allowed license.

`coverage_genres` uses the eight controlled genre families in `knowledge-status.json`; `genres` may remain more specific for retrieval. `creator_regions` describes relevant working/cultural context, not ethnicity or nationality inference. `historical_period` is `historical` for works made before 2000 and `contemporary` for works made in or after 2000. Record identity demographics only when an inspected institutional or first-party source supports them; do not guess from names or photographs.

### Critique pattern

Required fields in `critique-patterns.jsonl`:

- `method_tags`, `condition`, `visible_tests`, `likely_effect`;
- `counter_conditions`, `actions`, `exercise`;
- `source_ids`, `masterwork_ids`, `score_dimensions`;
- `scope`, `confidence`, `status`.

## Retrieval protocol

1. Finish the blind image scan before searching the knowledge base.
2. Convert the leading candidate into two to four method tags, such as `figure-ground`, `gesture`, `edge-control`, or `color-anchor`.
3. Search with `scripts/search_knowledge.py`; Chinese photography terms are expanded through the versioned `search-aliases.json` vocabulary while the original query terms remain active.
4. Search critique patterns first, then exact masterwork cards, then broader sources.
5. Prefer one strong method match over two famous but superficial matches.
6. Re-open the direct source page before giving a user a web link; registry verification can become stale.
7. State the meaningful difference between the reference and the user's image so the reference cannot become a copying recipe.

## Copyright and evidence boundaries

- Store metadata, links, short original analysis, and factual source scope; do not archive copyrighted course transcripts or image files.
- Mark translated or reposted material and trace it to the original creator where possible.
- Distinguish an official page's factual metadata from the coach's formal analysis.
- Do not infer consent, staging, factual accuracy, or ethical practice from an image alone.
- Never use inclusion in this database as evidence that an image is good or that a creator is authoritative.
