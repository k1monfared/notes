---
name: blog-edit-reader
description: Phase 7 of blog editing. Reader-facing passes: unanswered questions section, cold skeleton read, accessibility, and the takeaway read. Runs on the near-final draft, before publication.
version: 0.1.0
tags: [writing, editing, blog]
---

# Blog Edit: Reader facing (phase 7)

Anticipate the reader. Runs on the near-final draft.

## Sub-passes

1. **Unanswered questions.** Read as the standing reader. Write the questions the piece leaves open. Distinguish questions the piece raises on purpose (the standing aim wants those) from holes it forgot to fill. Only the holes are findings. Append the full list to the draft after a `---` separator at the very end.
2. **Skeleton read.** Read only the first line of each paragraph. If the piece does not still make sense, the structure has a gap; report it.
3. **Accessibility.** Alt text on every image, meaningful link text (never bare "here"), heading hierarchy.
4. **Takeaway read.** A no-context read of the near-final piece. In 2 to 3 sentences, state what you got from it. Append to the draft after the `---` separator, labeled: "what I think a general reader would think about this piece: ..." This is the gate before publication.

## Lifecycle

Both appended sections (unanswered questions, takeaway read) are working notes. They are stripped before publication by blog-edit-publish.

## Output

- `reader.log`: findings, skeleton read result, accessibility issues.
- The two appended sections in the draft.

## Edge cases

- The takeaway read must be honest to the reading, not flattering. If the piece confused you, say so in the 2-3 sentences.
- If the skeleton read fails, stop: route back to structure before polishing further.

## References

- Orchestrator: blog-edit
- Downstream: blog-edit-publish strips the appended sections
