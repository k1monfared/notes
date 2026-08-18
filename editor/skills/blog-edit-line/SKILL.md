---
name: blog-edit-line
description: Phase 6 of blog editing. Line-level passes in order: tone consistency, writer voice protection, line edit, repetition audit, jargon audit, rhythm, mechanics. Runs only after structure and integrity are done.
version: 0.1.0
tags: [writing, editing, blog]
---

# Blog Edit: Line level (phase 6)

Sentences that sound like the writer on their best day. Runs only after phases 4 and 5 are complete (ordering principle: never polish what might still move).

## Sub-passes, in order

1. **Tone consistency.** Flag register jumps. One voice per piece.
2. **Writer voice.** Protect the edge. Provocation, open endings, deliberate informal asides are not defects. Flag any proposed edit that would flatten the writer.
3. **Line edit.** Passive voice, filler, weak verbs, nominalizations. Tighten.
4. **Repetition audit.** Repeated words, phrases, sentence openings, sentence shapes. Enforce the aphorism budget: too many quotable lines and none of them land.
5. **Jargon audit.** Flag terms the standing reader will not know. Each flag resolves exactly one of three ways: explain, earn (context makes it clear), or cut.
6. **Rhythm.** Sentence and paragraph length variation. Read aloud; mark where you stumble.
7. **Mechanics.** Typos, contractions, number style, markdown correctness, house style (no em dashes, math as LaTeX).

## Output

- `lineedit.log`: every finding with id, location, and resolution.
- Approved edits applied to the draft, one changelog entry per edit.

## Worked example

From notes/blog/20260806_: "It's so over baby. lol jk, it isn't, and I wan't to explore how my old definition was worng." Mechanics: two typos. Voice: the register jump is deliberate; keep the aside, fix the spelling.

## Edge cases

- If tone keeper and voice keeper disagree, that is a dispute: run the convergence protocol (see blog-edit).
- Never edit the spine material's substance; clarity of expression only.

## References

- Orchestrator: blog-edit
- Upstream: blog-edit-structure, blog-edit-integrity
