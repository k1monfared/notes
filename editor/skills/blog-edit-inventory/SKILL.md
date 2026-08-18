---
name: blog-edit-inventory
description: Phase 1 of blog editing. Extracts the point map of a draft: main points, supporting points, side points (flavor, edge, human detail), and missing points. Use when starting an edit or after major restructuring.
version: 0.1.0
tags: [writing, editing, blog]
---

# Blog Edit: Inventory (phase 1)

Know what the piece is made of before changing anything. Read-only pass.

## Process

1. Read the whole draft and the workspace brief (if it exists).
2. Extract **main points**: the claims the piece exists to make. Usually one to three.
3. Extract **supporting points**: the evidence, arguments, and examples that carry each main point.
4. Extract **side points**: flavor, edge, human detail. The things that make this piece this writer's. Do not rank them as less important; they are often what readers remember.
5. Map every point to its paragraphs. Flag any paragraph claimed by no point (orphan) and any point with no paragraph (missing support).
6. List **missing points**: main, supporting, or side points the piece needs but does not have.
7. Write `points.log` in the workspace with the point map and the flags.

## Output format

One loglog list per category. Each point: one line, its paragraphs, and whether it is clear, buried, or rambling.

## Worked example

For notes/blog/20260806_ the three main points were: A (the old definition of mathematics is dead), B (the process of thinking is the product), C (importance is a social judgment that AI exposes). C became the spine.

## Edge cases

- A paragraph carrying two points is not automatically a problem; flag it only if the two points fight.
- Side points that do no work and add no flavor are candidates for the clarity pass to cut; note them, do not cut here.

## References

- Orchestrator: blog-edit
- Next pass: blog-edit-clarity
