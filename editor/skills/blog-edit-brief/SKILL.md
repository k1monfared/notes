---
name: blog-edit-brief
description: Phase 0 of blog editing. Infers the post's promise from the whole draft, drafts success criteria from the standing aim, and writes the workspace brief for human confirmation. Use when starting an edit or when the promise feels unclear.
version: 0.1.0
tags: [writing, editing, blog]
---

# Blog Edit: Brief (phase 0)

The brief is the yardstick for every later pass. It has three parts: reader, promise, success criteria.

## Standing reader profile (set once for the blog, do not re-derive)

- Interested in the topic, general audience
- Tolerates technical detail without needing to learn it
- Here for the argument and the conversation

## Standing aim (do not re-derive)

- Raise questions rather than answer them
- Make the reader wonder
- Multiple perspectives, leaning toward the conflicting ones
- Provocation is part of the writer's voice; titles may outspice the text by design
- Standards: correct, fact checked, flowing, supported

## Process

1. Read the whole draft.
2. Infer the promise in one sentence: what does the reader walk away with. The promise is inferred from the text, never imposed on it.
3. Draft success criteria from the promise plus the standing aim. Three to five bullets, each checkable.
4. Write or update `brief.log` in the workspace with reader profile, standing aim, promise, success criteria, and status line "awaiting human confirmation".
5. Present the promise to the human. Do not run later phases until the human confirms or corrects it.

## Worked example

For notes/blog/20260806_ the inferred promise was: "A tour of what happens to mathematics when proof production gets cheap, drawing the field as the author sees it, ending in a question rather than an answer."

## Edge cases

- If brief.log exists and is human-confirmed, do nothing; report the confirmed promise.
- If the draft is too rough to infer a promise, say so and propose two candidate promises for the human to pick from.

## References

- Orchestrator: blog-edit
- Standing profile source: /home/k1/public/notes/editor/docs/brief.log
